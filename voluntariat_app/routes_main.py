from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user
from . import task_manager
from .forms_message import IncidenceForm
from .helper import flash_info, labels, require_login
from .plugin_gmail import TaskIncidenceEmail

# Blueprint Configuration
main_bp = Blueprint(
    "main_bp", __name__, template_folder="templates", static_folder="static"
)

@main_bp.route("/", methods=["GET"])
def init():
    if current_user.is_authenticated:
        return redirect(url_for('volunteer_bp.dashboard'))
    else:
        return redirect(url_for("auth_bp.login"))

@main_bp.route('/incidence', methods=["GET", "POST"])
@require_login()
def incidence():
    form = IncidenceForm()
    form.type.choices = labels.get("incidences_types").split(',')
    if form.validate_on_submit():
        incidence_type = form.type.data
        incidence_description = form.description.data

        # send email
        email_task = TaskIncidenceEmail(
            incidence_user=current_user,
            incidence_type=incidence_type,
            incidence_description=incidence_description
        )
        task_manager.add_task(email_task)

        flash_info("incidence_saved")
        return redirect(url_for("main_bp.incidence"))

    return render_template('main-incidence.html',form=form,user=current_user)

@main_bp.route('/contact')
def contact():
    if current_user.is_authenticated:
        return redirect(url_for("main_bp.incidence"))
    else:
        return render_template('unregistered-contact.html')
