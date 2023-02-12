from flask import Blueprint, redirect, render_template, url_for, request
from flask_login import current_user, login_required
from .helper import flash_error, flash_info, load_volunteer, flash_warning, trim
from . import db, task_manager, params_manager, rewards_manager
from .forms_volunteer import ProfileForm, ChangePasswordForm, ShiftsForm, ShiftsFormWithPassword, DietForm, MealsForm, TicketsForm
from .plugin_gmail import TaskConfirmPasswordChangeEmail
from .models import Task, Shift, UserShift, UserDiet, UserMeal, Meal, Ticket, UserTicket
import sqlalchemy

# Blueprint Configuration
volunteer_bp = Blueprint(
    "volunteer_bp", __name__, template_folder="templates", static_folder="static"
)

@volunteer_bp.route("/v/<volunteer_hashid>", methods=["GET"])
@login_required
def volunteer(volunteer_hashid):
    if not current_user.is_admin or volunteer_hashid == current_user.hashid:
        return redirect(url_for('volunteer_bp.dashboard'))

    return redirect(url_for('admin_bp.profile', volunteer_hashid = volunteer_hashid))

@volunteer_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('volunteer-dashboard.html',user=current_user)

@volunteer_bp.route('/v/<volunteer_hashid>/profile', methods=["GET", "POST"])
@login_required
def profile(volunteer_hashid):
    # you can't change personal data of another person
    volunteer = load_volunteer(current_user,volunteer_hashid,allow_all_admins=False)
    if volunteer is None:
        if current_user.is_admin:
            return redirect(url_for('admin_bp.profile',volunteer_hashid=volunteer_hashid))

        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))

    form = ProfileForm(obj = volunteer)
    if form.validate_on_submit():
        form.populate_obj(volunteer)
        db.session.commit()
        flash_info("S'han actualitzat les dades")
        return redirect(url_for('volunteer_bp.profile',volunteer_hashid=volunteer_hashid))

    return render_template('volunteer-profile.html',form=form,volunteer=volunteer,user=current_user)

@volunteer_bp.route('/v/<volunteer_hashid>/password', methods=["GET", "POST"])
@login_required
def password(volunteer_hashid):
    # you can't change personal data of another person
    volunteer = load_volunteer(current_user,volunteer_hashid,allow_all_admins=False)
    if volunteer is None:
        if current_user.is_admin:
            return redirect(url_for('admin_bp.volunteer',volunteer_hashid=volunteer_hashid))

        flash_error("Adreça incorrecta")
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

            flash_info('Contrasenya actualitzada')
        else:
            flash_error("Contrasenya actual incorrecte. No s'ha canviat la contrasenya")

        return redirect(url_for('volunteer_bp.profile',volunteer_hashid=volunteer_hashid))

    return render_template('volunteer-password.html',form=form,volunteer=volunteer,user=current_user)

@volunteer_bp.route('/v/<volunteer_hashid>/tasks', methods=["GET", "POST"])
@login_required
def tasks(volunteer_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))

    # subquery que calcula quants torns té l'usuari per cada tasca
    count_subquery = sqlalchemy.text(f"""
        select s.task_id as task_id, count(u.user_id) as n_shifts
        from shifts as s left join 
            (select user_id, shift_id from user_shifts where user_id = {volunteer.id}) as u
        on s.id = u.shift_id group by s.task_id
    """).columns(task_id=db.Integer,n_shifts=db.Integer).subquery("count_subquery")

    tasks_and_number_of_shifts = db.session.query(
        Task, count_subquery.c.n_shifts
    ).join(
        count_subquery, Task.id == count_subquery.c.task_id
    ).order_by(
        Task.id.asc()
    )

    return render_template('volunteer-tasks.html',tasks_and_number_of_shifts=tasks_and_number_of_shifts,volunteer=volunteer,user=current_user)

@volunteer_bp.route('/v/<volunteer_hashid>/tasks/<int:task_id>', methods=["GET", "POST"])
@login_required
def shifts(volunteer_hashid, task_id):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))

    task = Task.query.filter_by(id = task_id).first()
    if task is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))
    
    read_only = __is_read_only(current_user)

    # els admins no necessiten password
    if task.password and not current_user.is_admin and not read_only:
        form = ShiftsFormWithPassword()
    else:
        form = ShiftsForm()

    if not read_only and form.validate_on_submit():
        # els admins no necessiten password
        if not current_user.is_admin and task.password and task.password != form.password.data:
            flash_warning("Contrasenya per apuntar-se a aquests torns incorrecta")
        else:
            __update_shifts(
                volunteer = volunteer,
                task_id = task_id,
                form = request.form
            )
            flash_info("S'han registrat els torns")

        return redirect(url_for('volunteer_bp.shifts',volunteer_hashid=volunteer_hashid,task_id=task_id))
    else:
        shifts_and_selected = __select_shifts_and_selected(volunteer_id=volunteer.id, task_id=task_id)

        if read_only:
            flash_info("S'ha bloquejat la modificació d'aquestes dades. Si hi ha algun problema, notifica una incidència.")
        
        return render_template('volunteer-shifts.html',
            form=form,
            read_only=read_only,
            task=task,
            shifts_and_selected=shifts_and_selected,
            volunteer=volunteer,
            user=current_user
        )

def __update_shifts(volunteer, task_id, form):
    # esborro tots els user_shifts d'aquest
    db.session.execute(f"""
        delete from user_shifts where user_id = {volunteer.id} 
        and shift_id in (select id from shifts where task_id = {task_id})
    """)        

    # afegeixo els torns
    for shift_id in form.getlist("shifts"):

        taked = db.session.execute(f"select count(*) from user_shifts where shift_id = {shift_id}").scalar()
        shift = Shift.query.filter_by(id = shift_id).first()

        # hi ha espai lliure!
        if shift is not None and (shift.slots <= 0 or shift.slots > taked):
            comments = trim(form.get(f"user-comments-{shift_id}"))
            user_shift = UserShift(
                user_id = volunteer.id,
                shift_id = int(shift_id),
                comments = comments
            )
            db.session.add(user_shift)
        else:
            flash_warning(f"No s'ha pogut registrar el torn: {shift.name}")

    current_shifts = UserShift.query.filter_by(user_id = volunteer.id).all()

    rewards_manager.update_tickets(
        user_id = volunteer.id,
        current_shifts = current_shifts
    )

    rewards_manager.update_meals(
        user_id = volunteer.id,
        current_shifts = current_shifts
    )

    db.session.commit()

def __select_shifts_and_selected(volunteer_id, task_id):
    # subquery que calcula, donat un usuari i una tasca, si ha seleccionat el torn (t/f) i les possibles observacions que ha posat
    selected_shifts_subquery = sqlalchemy.text(f"""
        select s.id as shift_id, COALESCE(c.taked,0) as taked, user_id is not null as selected, u.comments as comments 
        from shifts as s left join 
            (select shift_id, user_id, comments from user_shifts where user_id = {volunteer_id}) as u 
        on s.id = u.shift_id left join 
            (select shift_id, count(*) as taked from user_shifts group by shift_id) as c 
        on s.id = c.shift_id
        where s.task_id = {task_id}
    """).columns(shift_id=db.Integer,taked=db.Integer,selected=db.Boolean, comments=db.String).subquery("selected_shifts_subquery")

    return db.session.query(
        Shift, selected_shifts_subquery.c.taked, selected_shifts_subquery.c.selected, selected_shifts_subquery.c.comments, 
    ).join(
        selected_shifts_subquery, Shift.id == selected_shifts_subquery.c.shift_id
    ).order_by(
        Shift.id.asc()
    )

@volunteer_bp.route('/v/<volunteer_hashid>/meals', methods=["GET", "POST"])
@login_required
def meals(volunteer_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))

    read_only = __is_read_only(current_user)
    if not volunteer.has_shifts:
        flash_warning("Abans d'accedir a aquesta secció s'han de completar les Tasques i Torns")
        read_only = True

    diet = UserDiet.query.filter_by(user_id = volunteer.id).first()
    diet_form = DietForm(obj = diet)

    meals = Meal.query.all()
    user_meals = UserMeal.query.filter_by(user_id = volunteer.id).order_by(UserMeal.id.asc()).all()
    meals_form = __create_meals_form(meals = meals, user_meals = user_meals)

    if not read_only:
        if diet_form.validate_on_submit():
            # update de diet
            diet_form.populate_obj(diet)
            db.session.commit()
            flash_info("S'han registrat els canvis en la teva dieta")
            return redirect(url_for('volunteer_bp.meals',volunteer_hashid=volunteer_hashid))

        elif meals_form.validate_on_submit():
            # update de meals
            for um in user_meals:
                um.selected = meals_form[f"selected-{um.id}"].data
                if um.selected:
                    um.comments = meals_form[f"comments-{um.id}"].data
                else:
                    um.comments = ""

            db.session.commit()
            flash_info("S'han registrat els canvis en els teus àpats")
            return redirect(url_for('volunteer_bp.meals',volunteer_hashid=volunteer_hashid))

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
    
    setattr(F, "ids", [str(um.id) for um in user_meals])

    for um in user_meals:
        boolean_field = BooleanField(meals_dict[um.meal_id], default = um.selected)
        setattr(F, f"selected-{um.id}", boolean_field)

        text_area_field = TextAreaField(
            filters = [trim],
            default = um.comments
        )
        setattr(F, f"comments-{um.id}", text_area_field)

    return F()

@volunteer_bp.route('/v/<volunteer_hashid>/rewards', methods=["GET", "POST"])
@login_required
def rewards(volunteer_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))

    read_only = __is_read_only(current_user)
    if not volunteer.has_shifts:
        flash_warning("Abans d'accedir a aquesta secció s'han de completar les Tasques i Torns")
        read_only = True

    tickets = Ticket.query.all()
    user_tickets = UserTicket.query.filter_by(user_id = volunteer.id).order_by(UserTicket.id.asc()).all()
    tickets_form = __create_tickets_form(tickets = tickets, user_tickets = user_tickets)

    # if not read_only and tickets_form.validate_on_submit():
    #     # update de tickets
    #     for um in user_meals:
    #         um.selected = meals_form[f"selected-{um.id}"].data
    #         if um.selected:
    #             um.comments = meals_form[f"comments-{um.id}"].data
    #         else:
    #             um.comments = ""

    #     db.session.commit()
    #     flash_info("S'han registrat els canvis en els teus àpats")
    #     return redirect(url_for('volunteer_bp.meals',volunteer_hashid=volunteer_hashid))

    return render_template('volunteer-rewards.html',read_only=read_only,
        tickets_form=tickets_form,
        volunteer=volunteer,user=current_user
    )

def __create_tickets_form(tickets, user_tickets):
    from wtforms import BooleanField, TextAreaField

    if not user_tickets:
        return TicketsForm()

    tickets_dict = {}
    for m in tickets:
        tickets_dict[m.id] = m.name

    class F(TicketsForm):
        pass
    
    setattr(F, "ids", [str(ut.id) for ut in user_tickets])

    for ut in user_tickets:
        boolean_field = BooleanField(tickets_dict[ut.ticket_id], default = ut.selected)
        setattr(F, f"selected-{ut.id}", boolean_field)

        text_area_field = TextAreaField(
            filters = [trim],
            default = ut.comments
        )
        setattr(F, f"comments-{ut.id}", text_area_field)

    return F()

def __is_read_only(current_user):
    return not params_manager.allow_modifications and not current_user.is_admin