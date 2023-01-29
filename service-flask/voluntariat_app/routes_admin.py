from flask import Blueprint, redirect, render_template, url_for, request, Response, abort, stream_with_context
from flask_login import current_user, login_required
from .forms_message import EmailForm
from .helper import flash_error, flash_info, load_volunteer
from .models import User, Task, Shift, UserShift
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
    if not current_user.is_admin():
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    password_tasks = Task.query.filter(Task.password != '').order_by(Task.id.asc())

    invitation_url = params_manager.external_url + "/invitation/" + params_manager.invitation_token
    allow_modifications = params_manager.allow_modifications

    return render_template('admin-dashboard.html',
        invitation_url=invitation_url,allow_modifications=allow_modifications,
        password_tasks=password_tasks,
        user=current_user)

@admin_bp.route('/admin/volunteers')
@login_required
def people():
    if not current_user.is_admin():
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        file_name = hashid_manager.create_unique_file_name(
            id = current_user.id,
            name = "USERS",
            extension = ".xlsx"
        )
        select = """
            select surname as cognoms, name as nom, email, phone as mòbil, role as rol, ticket1, ticket2, ticket3, ticket4
            from users order by cognoms asc, nom asc
        """
        return generate_excel(select = select, file_name = file_name)
    else:
        volunteers = User.query.order_by(User.surname.asc(), User.name.asc()).all()

        return render_template('admin-volunteers.html', volunteers=volunteers,user=current_user)

@admin_bp.route("/admin/volunteers/<volunteer_hashid>", methods=["GET"])
@login_required
def profile(volunteer_hashid):
    if not current_user.is_admin():
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    volunteer = load_volunteer(current_user,volunteer_hashid)
    if volunteer is None:
        flash_error("Adreça incorrecta")
        return redirect(url_for('main_bp.init'))

    return render_template('admin-profile.html',volunteer=volunteer,user=current_user)

@admin_bp.route('/admin/volunteers/<volunteer_hashid>/message', methods=["GET", "POST"])
@login_required
def message(volunteer_hashid):
    if not current_user.is_admin():
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
    if not current_user.is_admin():
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    tasks = Task.query.order_by(Task.id.asc()).all()

    return render_template('admin-tasks.html',tasks=tasks,user=current_user)

@admin_bp.route('/admin/tasks/<int:task_id>')
@login_required
def shifts(task_id):
    if not current_user.is_admin():
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = f"""select t.name as tasca, s.name as torn,
            u.surname as cognoms, u.name as nom, u.email as email, u.phone as mòbil, us.user_comments as observacions 
            from users as u 
            join user_shifts as us on u.id = us.user_id
            join shifts as s on s.id = us.shift_id
            join tasks as t on t.id = s.task_id
            where t.id = {task_id}
            order by s.id asc, cognoms asc, nom asc"""

        file_name = hashid_manager.create_unique_file_name(
            id = current_user.id,
            name = f"TASK {task_id}",
            extension = ".xlsx"
        )
        return generate_excel(
            select=select,
            file_name=file_name
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
    if not current_user.is_admin():
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    excel = request.args.get('excel', default=False, type=bool)
    if excel:
        select = f"""select t.name as tasca, s.name as torn,
            u.surname as cognoms, u.name as nom, u.email as email, u.phone as mòbil, us.user_comments as observacions 
            from users as u 
            join user_shifts as us on u.id = us.user_id
            join shifts as s on s.id = us.shift_id
            join tasks as t on t.id = s.task_id
            where s.id = {shift_id}
            order by cognoms asc, nom asc"""

        file_name = hashid_manager.create_unique_file_name(
            id = current_user.id,
            name = f"TASK {task_id} SHIFT {shift_id}",
            extension = ".xlsx"
        )
        return generate_excel(
            select=select,
            file_name=file_name
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

    return render_template('admin-shift-volunteers.html',
        task=task,shift=shift,users_with_shifts=users_with_shifts,
        user=current_user
    )

@admin_bp.route('/admin/meals')
@login_required
def meals():
    if not current_user.is_admin():
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    return render_template('admin-meals.html',user=current_user)

@admin_bp.route('/admin/rewards')
@login_required
def rewards():
    if not current_user.is_admin():
        flash_error("Has de tenir un rol d'administrador per a visualitzar aquesta pàgina")
        return redirect(url_for('volunteer_bp.dashboard'))

    return render_template('admin-rewards.html',user=current_user)

def generate_excel(select, file_name):
    with excel_manager.create_excel(file_name) as excel:
        rows = db.session.execute(select)

        keys_to_upper = list(map(str.upper,rows._metadata.keys))
        excel.write(0, keys_to_upper)

        for row_index, row in enumerate(rows, start = 1):            
            excel.write(row_index, row)

    return redirect(url_for('admin_bp.download_excel',file_name=file_name))

@admin_bp.route('/excel/<file_name>')
@login_required
def download_excel(file_name):
    if not current_user.is_admin() or not file_name.endswith(".xlsx"):
        abort(404) 

    return Response(
        stream_with_context(excel_manager.stream_and_remove(file_name)),
        headers={'Content-Disposition': 'attachment', 'filename': file_name}
    )