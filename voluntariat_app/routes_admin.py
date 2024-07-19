from flask import Blueprint, redirect, render_template, url_for, request, Response, abort, stream_with_context
from flask_login import current_user
from .forms_message import EmailForm
from .forms_admin import AddWorkerForm, AddSomeWorkersForm, WorkerForm, AssignationsForm, TaskPasswordForm, ShiftSlotsForm
from .helper import flash_error, flash_info, load_volunteer, logger, get_shifts_meals_and_tickets, labels, get_shifts
from .helper import require_admin, require_superadmin
from .models import User, Task, Shift, UserShift, Meal, UserMeal, UserDiet, UserRewards, Ticket, UserTicket, UserRole
from . import db, hashid_manager, excel_manager, task_manager, params_manager, rewards_manager
from .plugin_gmail import TaskMessageEmail, TaskDefinitiveShiftsEmail
import sqlalchemy
from io import StringIO
from sqlalchemy import text

# Blueprint Configuration
admin_bp = Blueprint(
    "admin_bp", __name__, template_folder="templates", static_folder="static"
)

@admin_bp.route('/admin')
@require_admin()
def dashboard():
    invitation_url = params_manager.external_url + "/invitation/" + params_manager.invitation_token
    allow_modifications = params_manager.allow_modifications
    allow_volunteers = params_manager.allow_volunteers

    return render_template('admin-dashboard.html',
        invitation_url=invitation_url,
        allow_modifications=allow_modifications,
        allow_volunteers=allow_volunteers,
        user=current_user)

@admin_bp.route('/admin/p')
@admin_bp.route('/admin/people')
@require_admin()
def people():
    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        file_name = hashid_manager.create_unique_file_name(
            user_id = current_user.id,
            name = "PEOPLE",
            extension = ".xlsx"
        )
        select = """
            select surname as cognoms, name as nom, 
            case when role='worker' then '' else email end as email, 
            case when role='worker' then '' else dni end as dni, 
            phone as mòbil, role as rol, 
            case when shifts.n > 0 then 'X' else '' end as "amb torns",
            case when electrician then 'X' else '' end as electricitat,
            informative_meeting as "reunió informativa",
            purchased_ticket1 as "entrada adquirida 1",
            purchased_ticket2 as "entrada adquirida 2",
            purchased_ticket3 as "entrada adquirida 3"
            from users 
            left join (select user_id, count(*) as n from user_shifts group by user_id) as shifts
            on shifts.user_id = users.id
            where users.confirmed
            order by cognoms asc, nom asc, users.email asc
        """
        return generate_excel(file_name = file_name, select = select)
    else:
        volunteers = User.query.filter(User.confirmed).order_by(User.surname.asc(), User.name.asc(), User.id).all()
        not_confirmed = User.query.filter(User.confirmed == False).order_by(User.email.asc(), User.dni.asc(), User.id).all()
        return render_template('admin-people.html', volunteers=volunteers,not_confirmed=not_confirmed,user=current_user)

@admin_bp.route("/admin/p/<volunteer_hashid>", methods=["GET"])
@require_admin()
def profile(volunteer_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))
    elif volunteer.is_worker:
        return redirect(url_for('admin_bp.worker',worker_hashid=volunteer_hashid))

    (shifts, meals, tickets) = get_shifts_meals_and_tickets(volunteer.id)

    return render_template('admin-volunteer.html',shifts=shifts,meals=meals,tickets=tickets,volunteer=volunteer,user=current_user)

@admin_bp.route("/admin/worker", methods=["GET", "POST"])
@require_admin()
def add_worker():
    form = AddWorkerForm()
    form.shifts.choices = get_list_shifts()

    if form.validate_on_submit():
        worker = __insert_worker(
            0,
            admin_id = current_user.id,
            name = form.name.data,
            surname = form.surname.data,
            phone = form.phone.data,
            shift_id = int(form.shifts.data)
        )

        flash_info("worker_created")
        return redirect(url_for('admin_bp.profile',volunteer_hashid=worker.hashid))

    return render_template('admin-add-worker.html',form=form,user=current_user)

@admin_bp.route("/admin/workers", methods=["GET", "POST"])
@require_admin()
def add_some_workers():
    form = AddSomeWorkersForm()
    form.shifts.choices = get_list_shifts()

    if form.validate_on_submit():
        n = form.number.data
        prefix = form.prefix.data
        shift_id = int(form.shifts.data)

        for i in range(1,n+1):
            __insert_worker(
                i,
                admin_id = current_user.id,
                name = "",
                surname = f"{prefix} {i:02d}",
                phone = "",
                shift_id = shift_id
            )

        flash_info("some_workers_created")
        return redirect(url_for('admin_bp.people'))

    return render_template('admin-add-some-workers.html',form=form,user=current_user)

def __insert_worker(n, admin_id, surname, name, phone, shift_id):
    worker_token = f"{hashid_manager.create_token(admin_id)}#{n}#{admin_id}"
    worker = User(
        name = name,
        surname = surname,
        phone = phone,
        email = worker_token + "@worker",
        dni = worker_token,
        role = UserRole.worker
    )
    # random password pq no pot ser buit
    worker.set_password(worker_token + hashid_manager.create_password())

    logger.info(f"Nou treballador: {worker.full_name}")

    db.session.add(worker)
    db.session.commit()  # Create new user

    logger.info(f"Afegit treballador {worker.full_name} ")

    if shift_id > 0:
        # assigno automàticament aquest treballador a aquest torn
        shift = Shift.query.filter_by(id = shift_id).first()
        shift_assignations = [False for _ in shift.assignations]
        user_shift = UserShift(
            user_id = worker.id,
            shift_id = shift_id,
            shift_assignations = shift_assignations,
            comments = ""
        )
        db.session.add(user_shift)

    # guardo la informació de la seva dieta
    db.session.add(UserDiet(user_id = worker.id))
    db.session.add(UserRewards(user_id = worker.id))

    # actualitzo tickets, àpats i acreditacions
    rewards_manager.update_rewards(
        user = worker
    )

    db.session.commit() # guardem la dieta i les recompenses

    return worker

def get_list_shifts():
    no_shifts = [(0, labels.get("worker_without_shifts"))]
    db_shifts = [(id, t + ": " + s1 + ", " + s2) for (id, t, s1, s2) in 
        db.session.execute(text(f"""select s.id, t.name, s.day, s.description
            from tasks as t
            join shifts as s on t.id = s.task_id 
            order by t.id asc, s.id asc""")).all()
    ]
    return no_shifts + db_shifts

@admin_bp.route("/admin/worker/<worker_hashid>", methods=["GET", "POST"])
@require_admin()
def worker(worker_hashid):
    worker = load_volunteer(current_user,worker_hashid)
    if worker is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))
    elif not worker.is_worker:
        return redirect(url_for('admin_bp.profile',volunteer_hashid=worker_hashid))

    form = WorkerForm(obj = worker)
    if form.validate_on_submit():
        form.populate_obj(worker)
        db.session.add(worker)
        db.session.commit() # guardem els canvis
        flash_info("data_saved")
        redirect(request.full_path) # redirecció a mi mateix

    (shifts, meals, tickets) = get_shifts_meals_and_tickets(worker.id)

    return render_template('admin-worker.html',shifts=shifts,meals=meals,tickets=tickets,form=form,worker=worker,user=current_user)

@admin_bp.route('/admin/p/<volunteer_hashid>/message', methods=["GET", "POST"])
@require_admin()
def message(volunteer_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    form = EmailForm()
    if form.validate_on_submit():
        # send email
        email_task = TaskMessageEmail(
            user=volunteer,
            subject=form.subject.data,
            body=form.body.data
        )
        task_manager.add_task(email_task)

        flash_info("message_sent")
        return redirect(url_for('admin_bp.profile',volunteer_hashid=volunteer_hashid))

    return render_template('admin-message.html',form=form,volunteer=volunteer,user=current_user)

@admin_bp.route('/admin/tasks', methods=["GET", "POST"])
@require_admin()
def tasks():
    tasks = Task.query.order_by(Task.id.asc()).all()
    
    form = TaskPasswordForm()
    if form.validate_on_submit():
        for task in tasks:
            new_password = request.form.get(f"password-{task.id}", default=task.password, type=str)
            if new_password != task.password:
                task.password = new_password
                db.session.add(task)

        db.session.commit()

        flash_info("data_saved")
        redirect(request.full_path) # redirecció a mi mateix

    return render_template('admin-tasks.html',form=form,tasks=tasks,user=current_user)

@admin_bp.route('/admin/tasks/<int:task_id>', methods=["GET", "POST"])
@require_admin()
def shifts(task_id):
    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = """select t.name as tasca, s.day as dia, s.description as descripció,
            u.surname as cognoms, u.name as nom, 
            case when u.role='worker' then '' else u.email end as email, 
            u.phone as mòbil, us.comments as "obs torn"
            , case when us.shift_assignations[1] then s.assignations[1] else '' end as assignació
            , case when us.shift_assignations[2] then s.assignations[2] else '' end as assignació
            , case when us.shift_assignations[3] then s.assignations[3] else '' end as assignació
            from users as u 
            join user_shifts as us on u.id = us.user_id
            join shifts as s on s.id = us.shift_id
            join tasks as t on t.id = s.task_id
            where t.id = :TASK_ID
            order by s.id asc, cognoms asc, nom asc, u.email asc"""

        file_name = hashid_manager.create_unique_file_name(
            user_id = current_user.id,
            name = f"TASK {task_id}",
            extension = ".xlsx"
        )
        return generate_excel(
            file_name=file_name,
            select=select,
            params={"TASK_ID": task_id}
        )
    else:
        form = ShiftSlotsForm()
        if form.validate_on_submit():
            shifts = Shift.query.filter_by(task_id = task_id).all()
            for shift in shifts:
                shift.slots = request.form.get(f"slots-{shift.id}", default=shift.slots, type=int)
                db.session.add(shift)
            
            db.session.commit()

            flash_info("data_saved")
            redirect(request.full_path) # redirecció a mi mateix

        task = Task.query.filter_by(id = task_id).first()
        if task is None:
            flash_error("wrong_address")
            return redirect(url_for('main_bp.init'))

        count_subquery = sqlalchemy.text(f"""
            select shift_id, count(user_id) as n_shifts
            from user_shifts
            group by shift_id
        """).columns(shift_id=db.Integer,n_shifts=db.Integer).subquery("count_subquery")

        shifts_and_occupied = db.session.query(
            Shift, count_subquery.c.n_shifts, 
        ).outerjoin(
            count_subquery, Shift.id == count_subquery.c.shift_id
        ).where(
            Shift.task_id == task_id
        ).order_by(
            Shift.id.asc()
        )

    return render_template('admin-shifts.html',form=form,task=task,shifts_and_occupied=shifts_and_occupied,user=current_user)

@admin_bp.route('/admin/tasks/<int:task_id>/<int:shift_id>', methods=["GET", "POST"])
@require_admin()
def shift_detail(task_id, shift_id):
    task_and_shift = db.session.query(Task, Shift).join(Shift).filter(Shift.task_id == task_id, Shift.id == shift_id).first()
    if task_and_shift is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    task = task_and_shift[0]
    shift = task_and_shift[1]

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        assignations_select = StringIO()
        for (i, name) in enumerate(shift.assignations, start=1):
            assignations_select.write(f""",case when us.shift_assignations[{i}] then 'X' else '' end as "{name}"\n""")

        select = f"""select t.name as tasca, s.day as dia, s.description as descripció,
            u.surname as cognoms, u.name as nom, 
            case when u.role='worker' then '' else u.email end as email, 
            u.phone as mòbil, us.comments as "obs torn"
            {assignations_select.getvalue()}
            from users as u 
            join user_shifts as us on u.id = us.user_id
            join shifts as s on s.id = us.shift_id
            join tasks as t on t.id = s.task_id
            where s.id = :SHIFT_ID
            order by cognoms asc, nom asc, u.email asc"""

        file_name = hashid_manager.create_unique_file_name(
            user_id = current_user.id,
            name = f"TASK {task_id} SHIFT {shift_id}",
            extension = ".xlsx"
        )
        return generate_excel(
            file_name=file_name,
            select=select,
            params={"SHIFT_ID":shift_id}
        )

    form = AssignationsForm()
    if form.validate_on_submit():
        for i in range(len(shift.assignations)):
            volunteer_ids = ",".join(request.form.getlist(f"assignations-{i}"))
            # totes a FALSE
            db.session.execute(text(f"""update user_shifts set shift_assignations[{i+1}] = FALSE 
                where shift_id = {shift_id}"""
            ))
            # les triades, a TRUE
            if volunteer_ids:
                db.session.execute(text(f"""update user_shifts set shift_assignations[{i+1}] = TRUE 
                    where shift_id = {shift_id} and user_id in ({volunteer_ids})"""
                ))

        # actualitzo el cash de tots els voluntaris d'aquest torn
        user_shifts = db.session.query(UserShift).filter(UserShift.shift_id == shift_id).all()
        for us in user_shifts:
            rewards_manager.update_cash(us.user_id)

        db.session.commit()
        flash_info("assignations_saved")
        redirect(request.full_path) # redirecció a mi mateix

    users_with_shifts = db.session.query(User,UserShift).join(UserShift).filter(
        UserShift.shift_id == shift_id
    ).order_by(User.surname.asc(), User.name.asc()).all()

    return render_template('admin-shift-detail.html',
        task=task,shift=shift,users_with_shifts=users_with_shifts,
        form=form,user=current_user
    )

@admin_bp.route('/admin/tasks/<int:task_id>/email')
@require_superadmin()
def shifts_email(task_id):
    users = db.session.query(User).join(UserShift).join(Shift).filter(
        Shift.task_id == task_id
    ).all()

    for u in users:
        shifts = get_shifts(u.id)
        if len(shifts) > 0:
            task = TaskDefinitiveShiftsEmail(user = u, shifts = shifts)
            task_manager.add_task(task)

    flash_info("message_sent")

    return redirect(url_for('admin_bp.shifts', task_id = task_id))

@admin_bp.route('/admin/meals')
@require_admin()
def meals():
    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = """select m.day as dia, m.name as àpat,
            u.surname as cognoms, u.name as nom, 
            case when u.role='worker' then '' else u.email end as email, 
            u.phone as mòbil,
            um.comments as "obs àpat",
            case when ud.vegan then 'X' else '' end as vegana,
            case when ud.vegetarian then 'X' else '' end as vegetariana,
            case when ud.no_gluten then 'X' else '' end as "sense gluten",
            case when ud.no_lactose then 'X' else '' end as "sense lactosa",
            ud.comments as "obs dieta"
            from users as u 
            join user_meals as um on u.id = um.user_id
            join meals as m on m.id = um.meal_id
            join user_diets as ud on u.id = ud.user_id
            where um.selected
            order by m.day asc, m.id asc, cognoms asc, nom asc, u.email asc
        """

        file_name = hashid_manager.create_unique_file_name(
            user_id = current_user.id,
            name = "MEALS",
            extension = ".xlsx"
        )
        return generate_excel(
            file_name=file_name,
            select=select
        )

    count_subquery = sqlalchemy.text(f"""
        select meal_id, count(user_id) as n_meals
        from user_meals where selected
        group by meal_id
    """).columns(meal_id=db.Integer,n_meals=db.Integer).subquery("count_subquery")

    meals_and_quantity = db.session.query(
        Meal, count_subquery.c.n_meals, 
    ).outerjoin(
        count_subquery, Meal.id == count_subquery.c.meal_id
    ).order_by(
        Meal.id.asc()
    )

    return render_template('admin-meals.html',meals_and_quantity=meals_and_quantity,user=current_user)

@admin_bp.route('/admin/meals/<int:meal_id>')
@require_admin()
def meal_detail(meal_id):
    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = """select m.day as dia, m.name as àpat,
            u.surname as cognoms, u.name as nom, 
            case when u.role='worker' then '' else u.email end as email, 
            u.phone as mòbil,
            um.comments as "obs àpat",
            case when ud.vegan then 'X' else '' end as vegana,
            case when ud.vegetarian then 'X' else '' end as vegetariana,
            case when ud.no_gluten then 'X' else '' end as "sense gluten",
            case when ud.no_lactose then 'X' else '' end as "sense lactosa",
            ud.comments as "obs dieta"
            from users as u 
            join user_meals as um on u.id = um.user_id
            join meals as m on m.id = um.meal_id
            join user_diets as ud on u.id = ud.user_id
            where m.id = :MEAL_ID and um.selected
            order by cognoms asc, nom asc, u.email asc
        """

        file_name = hashid_manager.create_unique_file_name(
            user_id = current_user.id,
            name = f"MEAL {meal_id}",
            extension = ".xlsx"
        )
        return generate_excel(
            file_name=file_name,
            select=select,
            params={"MEAL_ID":meal_id}
        )

    meal = Meal.query.filter_by(id = meal_id).first()
    if meal is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    users_with_diet_and_meals = db.session.query(User, UserDiet, UserMeal).join(UserDiet).join(UserMeal).filter(
        UserMeal.meal_id == meal_id
    ).filter(
        UserMeal.selected
    ).order_by(User.surname.asc(), User.name.asc()).all()

    return render_template('admin-meal-detail.html',
        meal=meal,users_with_diet_and_meals=users_with_diet_and_meals,
        user=current_user
    )

@admin_bp.route('/admin/tickets')
@require_admin()
def tickets():
    day = request.args.get("day")
    if day is None:
        day = ""

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        day_filter = ""
        if day != "":
            # filtrem per dia incloent sempre els tickets que no tenen dia
            day_filter = f"where t.day='{day}' or t.day=''"

        select = f"""select t.day as dia, t.name as entrada,
            u.surname as cognoms, u.name as nom, 
            case when u.role='worker' then '' else u.email end as email, 
            u.phone as mòbil
            from users as u 
            join user_tickets as ut on u.id = ut.user_id
            join tickets as t on t.id = ut.ticket_id
            {day_filter}
            order by t.day asc, t.id asc, cognoms asc, nom asc, u.email asc
        """

        file_name = hashid_manager.create_unique_file_name(
            user_id = current_user.id,
            name = "ENTRADES-" + day,
            extension = ".xlsx"
        )
        return generate_excel(
            file_name=file_name,
            select=select
        )

    count_subquery = sqlalchemy.text(f"""
        select ticket_id, count(user_id) as n_tickets
        from user_tickets
        group by ticket_id
    """).columns(ticket_id=db.Integer,n_tickets=db.Integer).subquery("count_subquery")

    query_tickets_and_quantity = db.session.query(
        Ticket, count_subquery.c.n_tickets, 
    ).outerjoin(
        count_subquery, Ticket.id == count_subquery.c.ticket_id
    )

    if day != "":
        # filtrem per dia incloent sempre els tickets que no tenen dia
        query_tickets_and_quantity = query_tickets_and_quantity.filter((Ticket.day == day) | (Ticket.day == ''))

    tickets_and_quantity = query_tickets_and_quantity.order_by(
        Ticket.day.asc(), Ticket.id.asc()
    ).all()

    return render_template('admin-tickets.html',day=day,tickets_and_quantity=tickets_and_quantity,user=current_user)

@admin_bp.route('/admin/tickets/<int:ticket_id>')
@require_admin()
def tickets_detail(ticket_id):
    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = """select t.day as dia, t.name as entrada,
            u.surname as cognoms, u.name as nom, 
            case when u.role='worker' then '' else u.email end as email, 
            u.phone as mòbil
            from users as u 
            join user_tickets as ut on u.id = ut.user_id
            join tickets as t on t.id = ut.ticket_id
            where t.id = :TICKET_ID
            order by cognoms asc, nom asc, u.email asc
        """

        file_name = hashid_manager.create_unique_file_name(
            user_id = current_user.id,
            name = f"ENTRADA {ticket_id}",
            extension = ".xlsx"
        )
        return generate_excel(
            file_name=file_name,
            select=select,
            params={"TICKET_ID":ticket_id}
        )

    ticket = Ticket.query.filter_by(id = ticket_id).first()
    if ticket is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    users_with_tickets = db.session.query(User, UserTicket).join(UserTicket).filter(
        UserTicket.ticket_id == ticket_id
    ).order_by(User.surname.asc(), User.name.asc()).all()

    return render_template('admin-ticket-detail.html',
        ticket=ticket,users_with_tickets=users_with_tickets,
        user=current_user
    )

@admin_bp.route('/admin/rewards')
@require_admin()
def rewards():
    day = request.args.get("day")
    if day is None:
        day = ""

    excel = request.args.get('excel', default=False, type=bool)
    if excel:

        day_filter = ""
        if day != "":
            # filtrem per dia
            day_filter = f" and r.day='{day}'"

        select = f"""select r.day as dia,
            u.surname as cognoms, u.name as nom, 
            case when u.role='worker' then '' else u.email end as email, 
            u.phone as mòbil,
            r.cash as "tickets consum"
            from users as u 
            join (
                select user_id, (each(cash_by_day)).key as day, CAST((each(cash_by_day)).value AS INTEGER) as cash
                from user_rewards
            ) as r 
            on r.user_id = u.id
            where r.cash > 0
            {day_filter}
            order by dia asc, cognoms asc, nom asc, u.email asc
        """

        file_name = hashid_manager.create_unique_file_name(
            user_id = current_user.id,
            name = "CONSUM-" + day,
            extension = ".xlsx"
        )
        return generate_excel(
            file_name=file_name,
            select=select
        )

    cash_subquery = sqlalchemy.text(f"""
        select user_id, (each(cash_by_day)).key as day, CAST((each(cash_by_day)).value AS INTEGER) as cash
        from user_rewards
    """).columns(user_id=db.Integer,day=db.String,cash=db.Integer).subquery("cash_subquery")

    query_users_with_cash = db.session.query(
        User, cash_subquery.c.day, cash_subquery.c.cash, 
    ).join(
        cash_subquery, User.id == cash_subquery.c.user_id
    ).filter(
        cash_subquery.c.cash > 0
    )

    if day != "":
        # filtrem per dia
        query_users_with_cash = query_users_with_cash.filter(cash_subquery.c.day == day)

    users_with_cash = query_users_with_cash.order_by(cash_subquery.c.day.asc(), User.surname.asc(), User.name.asc()).all()

    return render_template('admin-cash.html',day=day,users_with_cash=users_with_cash,user=current_user)

@admin_bp.route('/admin/update-all-rewards')
@require_superadmin()
def update_all_rewards():
    rewards_manager.update_all_rewards()
    db.session.commit()
    flash_info("data_saved")
    return redirect(url_for('admin_bp.dashboard'))

@admin_bp.route('/admin/excel_tickets_and_rewards')
@require_admin()
def excel_tickets_and_rewards():
    day = request.args.get("day")
    if day is None:
        day = ""
    
    day_filter = ""
    day_aggregation = "t.day"
    if day != "":
        # filtrem per dia
        day_filter = f"where tr.day='{day}' or tr.day=''"
        # els abonaments surten cada dia
        day_aggregation = f"case when t.day = '' then '{day}' else t.day end"

    select = f"""select tr.day as dia, u.surname as cognoms, u.name as nom, 
        case when u.role='worker' then '' else u.email end as email, 
        u.phone as mòbil,
        tr.entrades as entrades,
        tr.cash as "tickets consum",
        case when tr.sopar then 'X' else '' end as "sopar",
        case when b.description is NULL then '' else b.description end as barres
        from users as u 
        join (
            select entrades, cash, sopar,
                case when t.user_id is NULL then r.user_id else t.user_id end as user_id,
                case when t.extended_day is NULL then r.day else t.extended_day end as day
            from (
                select ut.user_id as user_id, {day_aggregation} as extended_day, array_to_string(array_agg(t.name order by t.id),' + ') as entrades
                from tickets as t
                join user_tickets as ut on t.id = ut.ticket_id
                group by user_id, extended_day
            ) as t
            full outer join (
                select 
                    case when ur.user_id is NULL then sm.user_id else ur.user_id end as user_id,
                    case when ur.day is NULL then sm.day else ur.day end as day,
                    case when cash is NULL then 0 else cash end as cash,
                    case when selected then TRUE else FALSE end as sopar
                from (
                    select user_id, (each(cash_by_day)).key as day, CAST((each(cash_by_day)).value AS INTEGER) as cash
                    from user_rewards
                ) as ur
                full outer join (
                    select um.user_id, m.day, um.selected from meals as m join user_meals as um on m.id = um.meal_id
                    where um.selected
                ) as sm on ur.user_id = sm.user_id and ur.day = sm.day
            ) as r on r.user_id = t.user_id and r.day = t.extended_day
            where cash > 0 or entrades <> '' or sopar
        ) as tr on tr.user_id = u.id
        left join (
            select ush.user_id, sh.day, array_to_string(array_agg(sh.description order by sh.id),' + ') as description from shifts as sh join user_shifts as ush on sh.id = ush.shift_id
            where sh.task_id = 1
            group by ush.user_id, sh.day
        ) as b on b.user_id = u.id and b.day = tr.day
        {day_filter}
        order by cognoms asc, nom asc, u.email asc, tr.day asc;
    """
    # FIXME! sh.task_id = 1 és la tasca de barres!!!

    file_name = hashid_manager.create_unique_file_name(
        user_id = current_user.id,
        name = "TICKETS_I_CONSUM-" + day,
        extension = ".xlsx"
    )
    return generate_excel(
        file_name=file_name,
        select=select
    )

def generate_excel(file_name, select, params={}):
    with excel_manager.create_excel(file_name) as excel:
        rows = db.session.execute(text(select), params=params)

        keys_to_upper = list(map(str.upper,rows._metadata.keys))
        excel.write(0, keys_to_upper)

        for row_index, row in enumerate(rows, start = 1):            
            excel.write(row_index, row)

    return redirect(url_for('admin_bp.download_excel',file_name=file_name))

@admin_bp.route('/admin/excel/<file_name>')
@require_admin()
def download_excel(file_name):
    if not file_name.endswith(".xlsx"):
        abort(404) 

    return Response(
        stream_with_context(excel_manager.stream_and_remove(file_name)),
        headers={'Content-Disposition': 'attachment', 'filename': file_name}
    )