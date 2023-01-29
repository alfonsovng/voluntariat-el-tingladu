from flask import Blueprint, redirect, render_template, url_for, request
from flask_login import current_user, login_required
from .helper import flash_error, flash_info, load_volunteer, flash_warning, trim
from . import db, task_manager, params_manager
from .forms_volunteer import ProfileForm, ChangePasswordForm, ShiftsForm, ShiftsFormWithPassword
from .plugin_gmail import TaskConfirmPasswordChangeEmail
from .models import Task, Shift, UserShift
import sqlalchemy

# Blueprint Configuration
volunteer_bp = Blueprint(
    "volunteer_bp", __name__, template_folder="templates", static_folder="static"
)

@volunteer_bp.route("/v/<volunteer_hashid>", methods=["GET"])
@login_required
def volunteer(volunteer_hashid):
    if not current_user.is_admin() or volunteer_hashid == current_user.hashid:
        return redirect(url_for('volunteer_bp.dashboard'))

    return redirect(url_for('admin_bp.profile', volunteer_hashid = volunteer_hashid))

@volunteer_bp.route('/dashboard')
@login_required
def dashboard():
    allow_meals = has_meals(current_user.id)
    allow_rewards = has_rewards(current_user.id)

    return render_template('volunteer-dashboard.html',allow_meals=allow_meals,allow_rewards=allow_rewards,user=current_user)

@volunteer_bp.route('/v/<volunteer_hashid>/profile', methods=["GET", "POST"])
@login_required
def profile(volunteer_hashid):
    # you can't change personal data of another person
    volunteer = load_volunteer(current_user,volunteer_hashid,allow_all_admins=False)
    if volunteer is None:
        if current_user.is_admin():
            return redirect(url_for('admin_bp.volunteer',volunteer_hashid=volunteer_hashid))

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
        if current_user.is_admin():
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
    
    read_only = not params_manager.allow_modifications and not current_user.is_admin()

    # els admins no necessiten password
    if task.password and not current_user.is_admin() and not read_only:
        form = ShiftsFormWithPassword()
    else:
        form = ShiftsForm()

    if not read_only and form.validate_on_submit():

        # els admins no necessiten password
        if not current_user.is_admin() and task.password and task.password != form.password.data:
            flash_warning("Contrasenya per apuntar-se a aquests torns incorrecta")
        else:
            # esborro tots els user_shifts d'aquest
            db.session.execute(f"""
                delete from user_shifts where user_id = {volunteer.id} 
                and shift_id in (select id from shifts where task_id = {task_id})
            """)        

            # afegeixo els torns
            for shift_id in request.form.getlist("shifts"):

                taked = db.session.execute(f"select count(*) from user_shifts where shift_id = {shift_id}").scalar()
                shift = Shift.query.filter_by(id = shift_id).first()

                # hi ha espai lliure!
                if shift is not None and (shift.slots <= 0 or shift.slots > taked):
                    user_comments = trim(request.form.get(f"user-comments-{shift_id}"))
                    user_shift = UserShift(
                        user_id = volunteer.id,
                        shift_id = int(shift_id),
                        user_comments = user_comments
                    )
                    db.session.add(user_shift)
                else:
                    flash_warning(f"No s'ha pogut registrar el torn: {shift.name}")

            db.session.commit()

            flash_info("S'han registrat els torns")

        return redirect(url_for('volunteer_bp.shifts',volunteer_hashid=volunteer_hashid,task_id=task_id))
    else:
        # subquery que calcula, donat un usuari i una tasca, si ha seleccionat el torn (t/f) i les possibles observacions que ha posat
        selected_shifts_subquery = sqlalchemy.text(f"""
            select s.id as shift_id, COALESCE(c.taked,0) as taked, user_id is not null as selected, u.user_comments as user_comments 
            from shifts as s left join 
                (select shift_id, user_id, user_comments from user_shifts where user_id = {volunteer.id}) as u 
            on s.id = u.shift_id left join 
                (select shift_id, count(*) as taked from user_shifts group by shift_id) as c 
            on s.id = c.shift_id
            where s.task_id = {task_id}
        """).columns(shift_id=db.Integer,taked=db.Integer,selected=db.Boolean, user_comments=db.String).subquery("selected_shifts_subquery")

        shifts_and_selected = db.session.query(
            Shift, selected_shifts_subquery.c.taked, selected_shifts_subquery.c.selected, selected_shifts_subquery.c.user_comments, 
        ).join(
            selected_shifts_subquery, Shift.id == selected_shifts_subquery.c.shift_id
        ).order_by(
            Shift.id.asc()
        )

        if read_only:
            flash_info("S'ha bloquejat la modificació d'aquestes dades. Si hi ha algun problema, notifica una incidència.")
        
        return render_template('volunteer-shifts.html',form=form,
            read_only=read_only,
            task=task,shifts_and_selected=shifts_and_selected,
            volunteer=volunteer,user=current_user
        )

def has_meals(volunteer_id):
    n = db.session.execute(f"select count(*) from user_meals where user_id = {volunteer_id}").scalar()
    return n > 0

def has_rewards(volunteer_id):
    n = db.session.execute(f"select count(*) from user_rewards where user_id = {volunteer_id}").scalar()
    return n > 0

@volunteer_bp.route('/v/<volunteer_hashid>/meals', methods=["GET", "POST"])
@login_required
def meals(volunteer_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))

    if not has_meals(volunteer.id) and not current_user.is_admin():
        flash_warning("Abans d'accedir a aquesta secció has de completar les Tasques i Torns")

    return render_template('volunteer-meals.html',volunteer=volunteer,user=current_user)

@volunteer_bp.route('/v/<volunteer_hashid>/rewards', methods=["GET", "POST"])
@login_required
def rewards(volunteer_hashid):
    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))

    if not has_rewards(volunteer.id) and not current_user.is_admin():
        flash_warning("Abans d'accedir a aquesta secció has de completar les Tasques i Torns")

    return render_template('volunteer-rewards.html',volunteer=volunteer,user=current_user)