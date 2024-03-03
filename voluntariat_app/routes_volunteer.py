from flask import Blueprint, redirect, render_template, url_for, request
from flask_login import current_user
from .helper import flash_error, flash_info, load_volunteer, flash_warning, trim, get_shifts_meals_and_tickets
from .helper import require_login, require_view, is_read_only, labels
from . import db, task_manager, rewards_manager, hashid_manager
from .forms_volunteer import ProfileForm, ChangePasswordForm, ShiftsForm, ShiftsFormWithPassword, DietForm, MealsForm, TicketsForm, InformativeMeetingForm
from .plugin_gmail import TaskConfirmPasswordChangeEmail
from .models import Task, Shift, UserShift, UserDiet, UserMeal, Meal, UserRewards, UserTicket
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ARRAY
from urllib.request import pathname2url
from collections import OrderedDict
import random

# Blueprint Configuration
volunteer_bp = Blueprint(
    "volunteer_bp", __name__, template_folder="templates", static_folder="static"
)

@volunteer_bp.route('/p')
@require_login()
def redirect_to_dashboard():
    return redirect(url_for('volunteer_bp.dashboard'))

@volunteer_bp.route('/dashboard')
@require_login()
def dashboard():
    (shifts, meals, tickets) = get_shifts_meals_and_tickets(current_user.id)
    return render_template('volunteer-dashboard.html',shifts=shifts,meals=meals,tickets=tickets,user=current_user)

@volunteer_bp.route("/p/<volunteer_hashid>", methods=["GET"])
@require_login()
def volunteer(volunteer_hashid):
    if not current_user.is_admin or volunteer_hashid == current_user.hashid:
        return redirect(url_for('volunteer_bp.dashboard'))

    return redirect(url_for('admin_bp.profile', volunteer_hashid = volunteer_hashid))

@volunteer_bp.route('/p/<volunteer_hashid>/profile', methods=["GET", "POST"])
@require_login()
def profile(volunteer_hashid):
    # you can't change personal data of another person
    volunteer = load_volunteer(current_user,volunteer_hashid,allow_all_admins=False)
    if volunteer is None:
        if current_user.is_admin:
            return redirect(url_for('admin_bp.profile',volunteer_hashid=volunteer_hashid))

        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    form = ProfileForm(obj = volunteer)

    if form.validate_on_submit():
        form.populate_obj(volunteer)
        db.session.commit()
        flash_info("data_saved")
        return redirect(request.full_path) # redirecció a mi mateix

    return render_template('volunteer-profile.html',form=form,volunteer=volunteer,user=current_user)
    
@volunteer_bp.route('/p/<volunteer_hashid>/password', methods=["GET", "POST"])
@require_login()
def password(volunteer_hashid):
    # you can't change personal data of another person
    volunteer = load_volunteer(current_user,volunteer_hashid,allow_all_admins=False)
    if volunteer is None:
        if current_user.is_admin:
            return redirect(url_for('admin_bp.volunteer',volunteer_hashid=volunteer_hashid))

        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    form = ChangePasswordForm()
    if form.validate_on_submit():

        if volunteer.check_password(password=form.old_password.data):
            volunteer.change_password_token = None
            volunteer.set_password(form.new_password.data)
            db.session.commit() # set password an remove token

            # send email to confirm change
            email_task = TaskConfirmPasswordChangeEmail(name=volunteer.name,email=volunteer.email)
            task_manager.add_task(email_task)

            flash_info("change_password_successful")
        else:
            flash_error("current_password_error")

        return redirect(request.full_path) # redirecció a mi mateix

    return render_template('volunteer-password.html',form=form,volunteer=volunteer,user=current_user)

@volunteer_bp.route('/admin/p/<volunteer_hashid>/tasks', methods=["GET", "POST"])
@volunteer_bp.route('/p/<volunteer_hashid>/tasks', methods=["GET", "POST"])
@require_view()
def tasks(volunteer_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    # subquery que calcula quants torns té l'usuari per cada tasca
    count_subquery = text(f"""
        select s.task_id as task_id, count(u.user_id) as n_shifts
        from shifts as s left join 
            (select user_id, shift_id from user_shifts where user_id = {volunteer.id}) as u
        on s.id = u.shift_id group by s.task_id
    """).columns(task_id=db.Integer,n_shifts=db.Integer).subquery("count_subquery")

    if current_user.is_admin:
        tasks_and_number_of_shifts = db.session.query(
            Task, count_subquery.c.n_shifts
        ).join(
            count_subquery, Task.id == count_subquery.c.task_id
        ).order_by(
            Task.id.asc()
        )
    else:
        # si no es admin, sols veus les tasques de voluntari
        tasks_and_number_of_shifts = db.session.query(
            Task, count_subquery.c.n_shifts
        ).join(
            count_subquery, Task.id == count_subquery.c.task_id
        ).filter(
            Task.only_workers == False
        ).order_by(
            Task.id.asc()
        )

        # a mes, si no s'ha apuntat a cap tasca, no pot fer muntatge
        # FIXME!!!!
        if not volunteer.has_shifts:
            tasks_and_number_of_shifts = [(t,n) for (t,n) in tasks_and_number_of_shifts if t.name != 'MUNTATGE']

    # si té tasques de barra, ha d'anar a la reunió informativa
    informative_meeting_form = __get_informative_meeting_form(volunteer)

    return render_template('volunteer-tasks.html',informative_meeting_form=informative_meeting_form,tasks_and_number_of_shifts=tasks_and_number_of_shifts,volunteer=volunteer,user=current_user)

def __get_informative_meeting_form(volunteer):
    if volunteer.informative_meeting != "":
        form = InformativeMeetingForm(obj = volunteer)
        form.informative_meeting.choices = labels.get("information_meeting_types").split(',')
        form.informative_meeting.default = volunteer.informative_meeting
        return form
    return None

@volunteer_bp.route('/p/<volunteer_hashid>/change-informative-meeting', methods=["POST"])
@require_view()
def change_informative_meeting(volunteer_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    volunteer.informative_meeting = request.form.get("informative_meeting")
    db.session.add(volunteer)
    db.session.commit()
    flash_info("data_saved")

    return redirect(request.referrer or url_for('volunteer_bp.tasks',volunteer_hashid=volunteer_hashid))

@volunteer_bp.route('/admin/p/<volunteer_hashid>/tasks/<task_hashid>', methods=["GET", "POST"])
@volunteer_bp.route('/p/<volunteer_hashid>/tasks/<task_hashid>', methods=["GET", "POST"])
@require_view()
def task(volunteer_hashid, task_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))
    
    task_id = hashid_manager.get_task_id_from_hashid(task_hashid)
    if task_id is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    task = Task.query.filter_by(id = task_id).first()
    if task is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))
       
    days_and_number_of_shifts = [s for s in db.session.execute(text(f"""select s.day, count(us.user_id) 
        from shifts as s 
        left join (select shift_id, user_id from user_shifts where user_id = {volunteer.id}) as us 
        on us.shift_id = s.id where s.task_id = {task_id} group by s.day order by s.day"""))]

    if len(days_and_number_of_shifts) == 1:
        return redirect(request.path + "/shifts?day=" + pathname2url(days_and_number_of_shifts[0][0]))
    
    # si té tasques de barra, ha d'anar a la reunió informativa
    informative_meeting_form = __get_informative_meeting_form(volunteer)

    return render_template('volunteer-task.html',informative_meeting_form=informative_meeting_form, task=task, days_and_number_of_shifts=days_and_number_of_shifts,volunteer=volunteer,user=current_user)

@volunteer_bp.route('/admin/p/<volunteer_hashid>/tasks/<task_hashid>/shifts', methods=["GET", "POST"])
@volunteer_bp.route('/p/<volunteer_hashid>/tasks/<task_hashid>/shifts', methods=["GET", "POST"])
@require_view()
def shifts(volunteer_hashid, task_hashid):
    day = request.args.get("day")
    if day is None:
        day = ""

    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))
    
    task_id = hashid_manager.get_task_id_from_hashid(task_hashid)
    if task_id is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    task = Task.query.filter_by(id = task_id).first()
    if task is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))
    
    read_only = is_read_only()

    # els admins no necessiten password
    if task.password and not current_user.is_admin and not read_only:
        form = ShiftsFormWithPassword()
    else:
        form = ShiftsForm()

    if not read_only and form.validate_on_submit():
        # els admins no necessiten password
        if not current_user.is_admin and task.password and task.password != form.password.data:
            flash_warning("shift_password_error")
        else:
            __update_shifts(
                volunteer = volunteer,
                task_id = task_id,
                day = day,
                current_user_is_admin = current_user.is_admin,
                form = request.form
            )
            flash_info("data_saved")

        return redirect(request.full_path)
    else:
        shifts_and_selected = __select_shifts_and_selected(volunteer_id=volunteer.id, task_id=task_id, day=day)

        if not shifts_and_selected:
            # si hi ha 0 shifts es pq el day és incorrecte
            flash_error("wrong_address")
            return redirect(url_for('main_bp.init'))

        if read_only:
            flash_info("read_only")
        
        # si té tasques de barra, ha d'anar a la reunió informativa
        informative_meeting_form = __get_informative_meeting_form(volunteer)

        return render_template('volunteer-shifts.html',
            informative_meeting_form=informative_meeting_form,
            form=form,
            read_only=read_only,
            day = day,
            task=task,
            shifts_and_selected=shifts_and_selected,
            volunteer=volunteer,
            user=current_user
        )

def __update_shifts(volunteer, task_id, day, current_user_is_admin, form):
    current_user_shifts = UserShift.query.filter(UserShift.user_id == volunteer.id).filter(
        text(f"""shift_id in (select id from shifts where task_id = {task_id} and day = '{day}')""")
    ).all()

    shift_id_to_insert = set((int(id) for id in form.getlist("shifts")))

    for user_shift in current_user_shifts:
        if user_shift.shift_id in shift_id_to_insert:
            comments = trim(form.get(f"user-comments-{user_shift.shift_id}"))
            user_shift.comments = comments
            db.session.add(user_shift)

            # aquest no cal inserirlo
            shift_id_to_insert.remove(user_shift.shift_id)
        else:
            # l'esborrem
            db.session.delete(user_shift)

    # ara afegim tots els qui hi ha a shift_id_selected
    for shift_id in shift_id_to_insert:

        allow_user_shift = False
        shift = Shift.query.filter_by(id = shift_id).first()

        if current_user_is_admin:
            # els admins poden apuntar on sigui
            allow_user_shift = True
        elif shift.slots <= 0:
            # és un torn sense "tope"
            allow_user_shift = True
        else:
            # només si hi ha espai lliure!
            taked = db.session.execute(text(f"select count(*) from user_shifts where shift_id = {shift_id}")).scalar()
            allow_user_shift = shift.slots > taked

        if allow_user_shift:
            comments = trim(form.get(f"user-comments-{shift_id}"))
            shift_assignations = [False for _ in shift.assignations]
            user_shift = UserShift(
                user_id = volunteer.id,
                shift_id = int(shift_id),
                shift_assignations = shift_assignations,
                comments = comments
            )
            db.session.add(user_shift)
        else:
            flash_warning("not_all_shifts")

    # salvo els canvis per a poder comprovar si pot fer tasques de muntatge o ha d'anar a la reunió informativa
    db.session.commit()

    # si sols té tasques de muntatge i no és admin, tot fora
    if not current_user_is_admin:
        # FIXME: Dependencia xunga amb la tasca de MUNTATGE
        no_muntatge = db.session.execute(text(f"""select count(*) from user_shifts as us 
            join shifts as s on us.shift_id = s.id
            join tasks as t on s.task_id = t.id
            where us.user_id = {volunteer.id} and t.name != 'MUNTATGE'""")).scalar()
        if no_muntatge == 0:
            # esborro les possibles tasques de muntatge que té
            db.session.execute(text(f"""delete from user_shifts where user_id = {volunteer.id}"""))

    # FIXME: Si fa tasques de barra, ha d'anar a la reunió informativa
    tasques_barra = db.session.execute(text(f"""select count(*) from user_shifts as us 
            join shifts as s on us.shift_id = s.id
            join tasks as t on s.task_id = t.id
            where us.user_id = {volunteer.id} and t.name = 'BARRES'""")).scalar()
    if tasques_barra > 0:
        if volunteer.informative_meeting == "":
            # li assignem una reunió informativa a l'atzar
            options = labels.get("information_meeting_types").split(',')
            options.pop() # el darrer element és "no puc anar" i no el triem
            # el guardo al perfil
            volunteer.informative_meeting = random.choice(options)
            flash_info("informative_meeting_assigned")
    else:
        # no té tasques de barra, per tant no cal que vagi a la reunió informativa
        volunteer.informative_meeting = ""

    # actualitzo tickets, àpats i acreditacions
    rewards_manager.update_rewards(
        user = volunteer
    )

    db.session.commit()

def __select_shifts_and_selected(volunteer_id, task_id, day):
    # subquery que calcula, donat un usuari i una tasca, si ha seleccionat el torn (t/f) i les possibles observacions que ha posat
    selected_shifts_subquery = text(f"""
        select s.id as shift_id, COALESCE(c.taked,0) as taked, user_id is not null as selected, u.comments as comments, s.assignations as assignations, u.shift_assignations as shift_assignations 
        from shifts as s left join 
            (select shift_id, user_id, comments, shift_assignations from user_shifts where user_id = {volunteer_id}) as u 
        on s.id = u.shift_id left join 
            (select shift_id, count(*) as taked from user_shifts group by shift_id) as c 
        on s.id = c.shift_id
        where s.task_id = {task_id} and s.day = '{day}'
    """).columns(shift_id=db.Integer,taked=db.Integer,selected=db.Boolean, comments=db.String, assignations=ARRAY(db.String), shift_assignations=ARRAY(db.Boolean)).subquery("selected_shifts_subquery")

    return db.session.query(
        Shift, selected_shifts_subquery.c.taked, selected_shifts_subquery.c.selected, selected_shifts_subquery.c.comments, selected_shifts_subquery.c.assignations, selected_shifts_subquery.c.shift_assignations
    ).join(
        selected_shifts_subquery, Shift.id == selected_shifts_subquery.c.shift_id
    ).order_by(
        Shift.id.asc()
    ).all()

@volunteer_bp.route('/admin/p/<volunteer_hashid>/meals', methods=["GET", "POST"])
@volunteer_bp.route('/p/<volunteer_hashid>/meals', methods=["GET", "POST"])
@require_view()
def meals(volunteer_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    read_only = is_read_only()
    if read_only:
        flash_info("read_only")
    elif not volunteer.has_shifts:
        flash_warning("first_tasks_and_shifts")
        read_only = True

    diet = UserDiet.query.filter_by(user_id = volunteer.id).first()
    diet_form = DietForm(obj = diet)

    meals = Meal.query.all()
    user_meals = UserMeal.query.filter_by(user_id = volunteer.id).order_by(UserMeal.meal_id.asc()).all()
    meals_form = __create_meals_form(meals = meals, user_meals = user_meals)

    if not read_only:
        if diet_form.validate_on_submit():
            # update de diet
            diet_form.populate_obj(diet)
            db.session.commit()
            flash_info("data_saved")
            return redirect(request.full_path) # redirecció a mi mateix

        elif meals_form.validate_on_submit():
            # update de meals
            for um in user_meals:
                um.selected = meals_form[f"selected-{um.meal_id}"].data
                if um.selected:
                    um.comments = meals_form[f"comments-{um.meal_id}"].data
                else:
                    um.comments = ""

            db.session.commit()
            flash_info("data_saved")
            return redirect(request.full_path) # redirecció a mi mateix

    return render_template('volunteer-meals.html',read_only=read_only,
        diet_form=diet_form,meals_form=meals_form,
        volunteer=volunteer,user=current_user
    )

def __create_meals_form(meals, user_meals):
    from wtforms import BooleanField, TextAreaField

    if not user_meals:
        return MealsForm()

    meals_dict = {}
    for m in meals:
        meals_dict[m.id] = m.name

    class F(MealsForm):
        pass
    
    setattr(F, "meal_ids", [str(um.meal_id) for um in user_meals])

    for um in user_meals:
        boolean_field = BooleanField(meals_dict[um.meal_id], default = um.selected)
        setattr(F, f"selected-{um.meal_id}", boolean_field)

        text_area_field = TextAreaField(
            filters = [trim],
            default = um.comments
        )
        setattr(F, f"comments-{um.meal_id}", text_area_field)

    return F()

@volunteer_bp.route('/admin/p/<volunteer_hashid>/rewards', methods=["GET", "POST"])
@volunteer_bp.route('/p/<volunteer_hashid>/rewards', methods=["GET", "POST"])
@require_view()
def rewards(volunteer_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("wrong_address")
        return redirect(url_for('main_bp.init'))

    read_only = is_read_only()
    if not volunteer.has_shifts:
        flash_warning("first_tasks_and_shifts")
        read_only = True

    volunteer_tickets = db.session.query(UserTicket).filter(
            UserTicket.user_id == volunteer.id
        ).order_by(UserTicket.ticket_id.asc()).all()
    
    form = TicketsForm()
    if not read_only and form.validate_on_submit():
        # canvio els tickets seleccionats
        for ut in volunteer_tickets:
            new_ticket_id_raw = request.form.get(f"ticket-{ut.ticket_id}")
            if new_ticket_id_raw is not None:
                new_ticket_id = int(new_ticket_id_raw)
                if new_ticket_id != ut.ticket_id and new_ticket_id in ut.ticket_id_options:
                    ut.ticket_id = new_ticket_id
                    db.session.add(ut)

        db.session.commit()
        flash_info("data_saved")
        return redirect(request.full_path) # redirecció a mi mateix
    else:
        rewards = UserRewards.query.filter_by(user_id = volunteer.id).first()

        total_cash = 0
        for c in rewards.cash_by_day.values():
            total_cash += int(c)

        all_tickets = {id:name for (id, name) in db.session.execute(text(f"""select id, name from tickets"""))}
        tickets = [(ut.ticket_id, [(id, all_tickets[id]) for id in ut.ticket_id_options]) for ut in volunteer_tickets]

        # si no hi ha opcions, no mostro el botó de submit
        any_options = False
        for (_, options) in tickets:
            if len(options) > 1:
                any_options = True
                break

        return render_template('volunteer-rewards.html',
            form = form,
            read_only = read_only,
            any_options = any_options,
            tickets = tickets,
            cash_descriptions = rewards.description,
            cash_by_day = OrderedDict(sorted(rewards.cash_by_day.items())),
            total_cash = total_cash,
            volunteer = volunteer, user = current_user
        )
