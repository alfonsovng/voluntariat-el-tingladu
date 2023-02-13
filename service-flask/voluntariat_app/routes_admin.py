from flask import Blueprint, redirect, render_template, url_for, request, Response, abort, stream_with_context
from flask_login import current_user, login_required
from .forms_message import EmailForm
from .forms_worker import NewWorkerForm, WorkerForm
from .helper import flash_error, flash_info, load_volunteer, logger, get_timestamp
from .models import User, Task, Shift, UserShift, Meal, UserMeal, UserDiet, Ticket, UserTicket, UserRole
from . import db, hashid_manager, excel_manager, task_manager, params_manager
from .plugin_gmail import TaskMessageEmail
import sqlalchemy

# Blueprint Configuration
admin_bp = Blueprint(
    "admin_bp", __name__, template_folder="templates", static_folder="static"
)

@admin_bp.route('/admin')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    password_tasks = Task.query.filter(Task.password != '').order_by(Task.id.asc())

    invitation_url = params_manager.external_url + "/invitation/" + params_manager.invitation_token
    allow_modifications = params_manager.allow_modifications

    return render_template('admin-dashboard.html',
        invitation_url=invitation_url,allow_modifications=allow_modifications,
        password_tasks=password_tasks,
        user=current_user)

@admin_bp.route('/admin/people')
@login_required
def people():
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        file_name = hashid_manager.create_unique_file_name(
            id = current_user.id,
            name = "PEOPLE",
            extension = ".xlsx"
        )
        select = """
            select surname as cognoms, name as nom, 
            case when role='worker' then '' else email end as email, 
            case when role='worker' then '' else dni end as dni, 
            phone as mòbil, role as rol, 
            case when electrician then 'X' else '' end as electricitat,
            purchased_ticket1 as "entrada adquirida"
            from users order by cognoms asc, nom asc
        """
        return generate_excel(file_name = file_name, select = select)
    else:
        volunteers = User.query.order_by(User.surname.asc(), User.name.asc()).all()

        return render_template('admin-people.html', volunteers=volunteers,user=current_user)

@admin_bp.route("/admin/people/<volunteer_hashid>", methods=["GET"])
@login_required
def profile(volunteer_hashid):
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))
    elif volunteer.is_worker:
        return redirect(url_for('admin_bp.worker',worker_hashid=volunteer_hashid))

    shifts = [s for s in db.session.execute(f"""select t.name || ': ' || s.name 
        from tasks as t 
        join shifts as s on t.id = s.task_id 
        join user_shifts as us on us.shift_id = s.id 
        where us.user_id = {volunteer.id}""").scalars()]
    meals = [m for m in db.session.execute(f"""select m.name 
        from meals as m 
        join user_meals as um on m.id=um.meal_id 
        where um.selected and um.user_id = {volunteer.id}""").scalars()]
    tickets = [t for t in db.session.execute(f"""select t.name 
        from tickets as t 
        join user_tickets as ut on t.id=ut.ticket_id 
        where ut.selected and ut.user_id = {volunteer.id}""").scalars()]

    return render_template('admin-volunteer.html',shifts=shifts,meals=meals,tickets=tickets,volunteer=volunteer,user=current_user)

@admin_bp.route("/admin/worker", methods=["GET", "POST"])
@login_required
def new_worker():
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    form = NewWorkerForm()
    if form.validate_on_submit():
        worker = User()
        form.populate_obj(worker)

        logger.info(f"Nou treballador: {worker.full_name}")

        worker.dni = f"{get_timestamp()}#{current_user.id}"
        worker.role = UserRole.worker
        # random email pq no pot ser buit
        worker.email = hashid_manager.create_token(current_user.id) + params_manager.worker_fake_email_domain
        # random password pq no pot ser buit
        worker.set_password(hashid_manager.create_password())
       
        db.session.add(worker)
        db.session.commit()  # Create new user

        # guardo la informació de la seva dieta
        db.session.add(UserDiet(user_id = worker.id))

        db.session.commit() # guardem la dieta
        flash_info('Persona treballadora creada')
        return redirect(url_for('admin_bp.profile',volunteer_hashid=worker.hashid))

    return render_template('admin-new-worker.html',form=form,user=current_user)

@admin_bp.route("/admin/worker/<worker_hashid>", methods=["GET", "POST"])
@login_required
def worker(worker_hashid):
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    worker = load_volunteer(current_user,worker_hashid)
    if worker is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))
    elif not worker.is_worker:
        return redirect(url_for('admin_bp.profile',volunteer_hashid=worker_hashid))

    form = WorkerForm(obj = worker)
    if form.validate_on_submit():
        form.populate_obj(worker)
        db.session.add(worker)
        db.session.commit() # guardem els canvis
        flash_info('Dades actualitzades')
        return redirect(url_for('admin_bp.worker',worker_hashid=worker_hashid))

    shifts = [s for s in db.session.execute(f"""select t.name || ': ' || s.name 
        from tasks as t 
        join shifts as s on t.id = s.task_id 
        join user_shifts as us on us.shift_id = s.id 
        where us.user_id = {worker.id}""").scalars()]
    meals = [m for m in db.session.execute(f"""select m.name 
        from meals as m 
        join user_meals as um on m.id=um.meal_id 
        where um.selected and um.user_id = {worker.id}""").scalars()]
    tickets = [t for t in db.session.execute(f"""select t.name 
        from tickets as t 
        join user_tickets as ut on t.id=ut.ticket_id 
        where ut.selected and ut.user_id = {worker.id}""").scalars()]

    return render_template('admin-worker.html',shifts=shifts,meals=meals,tickets=tickets,form=form,worker=worker,user=current_user)

@admin_bp.route('/admin/people/<volunteer_hashid>/message', methods=["GET", "POST"])
@login_required
def message(volunteer_hashid):
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("Adreça incorrecta")
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

        flash_info('Missatge enviat')
        return redirect(url_for('admin_bp.profile',volunteer_hashid=volunteer_hashid))

    return render_template('admin-message.html',form=form,volunteer=volunteer,user=current_user)

@admin_bp.route('/admin/tasks')
@login_required
def tasks():
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    tasks = Task.query.order_by(Task.id.asc()).all()

    return render_template('admin-tasks.html',tasks=tasks,user=current_user)

@admin_bp.route('/admin/tasks/<int:task_id>')
@login_required
def shifts(task_id):
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = f"""select t.name as tasca, s.name as torn,
            u.surname as cognoms, u.name as nom, u.email as email, u.phone as mòbil, us.comments as "obs torn" 
            from users as u 
            join user_shifts as us on u.id = us.user_id
            join shifts as s on s.id = us.shift_id
            join tasks as t on t.id = s.task_id
            where t.id = :TASK_ID
            order by s.id asc, cognoms asc, nom asc"""

        file_name = hashid_manager.create_unique_file_name(
            id = current_user.id,
            name = f"TASK {task_id}",
            extension = ".xlsx"
        )
        return generate_excel(
            file_name=file_name,
            select=select,
            params={"TASK_ID": task_id}
        )
    else:
        task = Task.query.filter_by(id = task_id).first()
        if task is None:
            flash_error("Adreça incorrecta")
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

    return render_template('admin-shifts.html',task=task,shifts_and_occupied=shifts_and_occupied,user=current_user)

@admin_bp.route('/admin/tasks/<int:task_id>/<int:shift_id>', methods=["GET", "POST"])
@login_required
def shift_detail(task_id, shift_id):
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = f"""select t.name as tasca, s.name as torn,
            u.surname as cognoms, u.name as nom, u.email as email, u.phone as mòbil, us.comments as "obs torn" 
            from users as u 
            join user_shifts as us on u.id = us.user_id
            join shifts as s on s.id = us.shift_id
            join tasks as t on t.id = s.task_id
            where s.id = :SHIFT_ID
            order by cognoms asc, nom asc"""

        file_name = hashid_manager.create_unique_file_name(
            id = current_user.id,
            name = f"TASK {task_id} SHIFT {shift_id}",
            extension = ".xlsx"
        )
        return generate_excel(
            file_name=file_name,
            select=select,
            params={"SHIFT_ID":shift_id}
        )

    task_and_shift = db.session.query(Task, Shift).join(Shift).filter(Shift.task_id == task_id, Shift.id == shift_id).first()
    if task_and_shift is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))

    task = task_and_shift[0]
    shift = task_and_shift[1]

    users_with_shifts = db.session.query(User,UserShift).join(UserShift).filter(
        UserShift.shift_id == shift_id
    ).order_by(User.surname.asc(), User.name.asc()).all()

    return render_template('admin-shift-detail.html',
        task=task,shift=shift,users_with_shifts=users_with_shifts,
        user=current_user
    )

@admin_bp.route('/admin/meals')
@login_required
def meals():
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = f"""select m.name as àpat,
            u.surname as cognoms, u.name as nom, u.email as email, u.phone as mòbil,
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
            order by m.id asc, cognoms asc, nom asc
        """

        file_name = hashid_manager.create_unique_file_name(
            id = current_user.id,
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
@login_required
def meal_detail(meal_id):
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = f"""select m.name as àpat,
            u.surname as cognoms, u.name as nom, u.email as email, u.phone as mòbil,
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
            order by cognoms asc, nom asc
        """

        file_name = hashid_manager.create_unique_file_name(
            id = current_user.id,
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
        flash_error("Adreça incorrecta")
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
@login_required
def tickets():
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = f"""select t.name as ticket,
            u.surname as cognoms, u.name as nom, u.email as email, u.phone as mòbil,
            ut.comments as "obs entrada"
            from users as u 
            join user_tickets as ut on u.id = ut.user_id
            join tickets as t on t.id = ut.ticket_id
            where ut.selected
            order by t.id asc, cognoms asc, nom asc
        """

        file_name = hashid_manager.create_unique_file_name(
            id = current_user.id,
            name = "TICKETS",
            extension = ".xlsx"
        )
        return generate_excel(
            file_name=file_name,
            select=select
        )

    count_subquery = sqlalchemy.text(f"""
        select ticket_id, count(user_id) as n_tickets
        from user_tickets where selected
        group by ticket_id
    """).columns(ticket_id=db.Integer,n_tickets=db.Integer).subquery("count_subquery")

    tickets_and_quantity = db.session.query(
        Ticket, count_subquery.c.n_tickets, 
    ).outerjoin(
        count_subquery, Ticket.id == count_subquery.c.ticket_id
    ).order_by(
        Ticket.id.asc()
    )

    return render_template('admin-tickets.html',tickets_and_quantity=tickets_and_quantity,user=current_user)

@admin_bp.route('/admin/tickets/<int:ticket_id>')
@login_required
def tickets_detail(ticket_id):
    if not current_user.is_admin:
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = f"""select t.name as ticket,
            u.surname as cognoms, u.name as nom, u.email as email, u.phone as mòbil,
            ut.comments as "obs entrada"
            from users as u 
            join user_tickets as ut on u.id = ut.user_id
            join tickets as t on t.id = ut.ticket_id
            where t.id = :TICKET_ID and ut.selected
            order by t.id asc, cognoms asc, nom asc
        """

        file_name = hashid_manager.create_unique_file_name(
            id = current_user.id,
            name = f"TICKET {ticket_id}",
            extension = ".xlsx"
        )
        return generate_excel(
            file_name=file_name,
            select=select,
            params={"TICKET_ID":ticket_id}
        )

    ticket = Ticket.query.filter_by(id = ticket_id).first()
    if ticket is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))

    users_with_tickets = db.session.query(User, UserTicket).join(UserTicket).filter(
        UserTicket.ticket_id == ticket_id
    ).filter(
        UserTicket.selected
    ).order_by(User.surname.asc(), User.name.asc()).all()

    return render_template('admin-ticket-detail.html',
        ticket=ticket,users_with_tickets=users_with_tickets,
        user=current_user
    )

def generate_excel(file_name, select, params={}):
    with excel_manager.create_excel(file_name) as excel:
        rows = db.session.execute(select, params=params)

        keys_to_upper = list(map(str.upper,rows._metadata.keys))
        excel.write(0, keys_to_upper)

        for row_index, row in enumerate(rows, start = 1):            
            excel.write(row_index, row)

    return redirect(url_for('admin_bp.download_excel',file_name=file_name))

@admin_bp.route('/excel/<file_name>')
@login_required
def download_excel(file_name):
    if not current_user.is_admin or not file_name.endswith(".xlsx"):
        abort(404) 

    return Response(
        stream_with_context(excel_manager.stream_and_remove(file_name)),
        headers={'Content-Disposition': 'attachment', 'filename': file_name}
    )