from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from . import login_manager, db, hashid_manager, task_manager, params_manager
from .forms_auth import LoginForm, SignUpForm, ForgottenPasswordForm, ResetPasswordForm
from .models import User, UserRole, UserDiet, UserRewards
from .plugin_gmail import TaskSignUpEmail, TaskResetPasswordEmail, TaskConfirmPasswordChangeEmail
from .helper import flash_info, flash_warning, flash_error, logger

# Blueprint Configuration
auth_bp = Blueprint(
    "auth_bp", __name__, template_folder="templates", static_folder="static"
)

@auth_bp.route("/invitation", defaults={'invitation_token': None}, methods=["GET", "POST"])
@auth_bp.route("/invitation/<invitation_token>", methods=["GET", "POST"])
@auth_bp.route("/sign-up", defaults={'invitation_token': None}, methods=["GET", "POST"])
@auth_bp.route("/sign-up/<invitation_token>", methods=["GET", "POST"])
def signup(invitation_token):
    # Bypass if user is logged in
    if current_user.is_authenticated:
        return redirect(url_for("main_bp.init"))
    
    if params_manager.invitation_token: # not empty
        if invitation_token is None:
            flash_warning("no_invitation")
            return redirect(url_for("main_bp.contact"))
        elif invitation_token != params_manager.invitation_token:
            flash_warning("wrong_invitation")
            return redirect(url_for("main_bp.contact"))

    form = SignUpForm()
    # Validate sign up attempt
    if form.validate_on_submit():
        lowercase_email = form.email.data.lower()

        existing_user = User.query.filter_by(email=lowercase_email).first()
        if existing_user is None:

            logger.info(f"Nou voluntari: {lowercase_email}")

            user = User(
                name=form.name.data,
                surname=form.surname.data,
                email=lowercase_email,
                dni=form.dni.data,
                phone=form.phone.data,
                electrician = form.electrician.data,
                role=UserRole.volunteer
            )
            # set a random password because it can't be null
            user.set_password(hashid_manager.create_password())
            db.session.add(user)
            db.session.commit()  # Create new user

            # create token with the user id
            token = hashid_manager.create_token(user.id)
            user.change_password_token = token
            db.session.add(user)
            
            # guardo la informació de la seva dieta i les seves recompenses
            db.session.add(UserDiet(user_id = user.id))
            db.session.add(UserRewards(user_id = user.id))

            db.session.commit() # guardem token, dieta i recompenses
           
            # send email to end signup
            email_task = TaskSignUpEmail(name=form.name.data,email=lowercase_email,token=token)
            task_manager.add_task(email_task)

            flash_info("sign_up_successful")
            return redirect(url_for("auth_bp.login"))

        # user exists
        flash_warning("sign_up_error")
        
    return render_template('unregistered-sign-up.html', form = form)

@auth_bp.route("/forgotten-password", methods=["GET", "POST"])
def forgotten_password():
    # Bypass if user is logged in
    if current_user.is_authenticated:
        return redirect(url_for("main_bp.init"))

    form = ForgottenPasswordForm()
    # Validate sign up attempt
    if form.validate_on_submit():
        lowercase_email = form.email.data.lower()

        existing_user = User.query.filter_by(email=lowercase_email).first()
        if existing_user is not None:

            token = hashid_manager.create_token(existing_user.id)
            existing_user.change_password_token = token   
            db.session.commit()  # add token
           
            # send email to reset password
            email_task = TaskResetPasswordEmail(name=existing_user.name,email=lowercase_email,token=token)
            task_manager.add_task(email_task)

            flash_info("reset_password_successful")
            return redirect(url_for("auth_bp.login"))

        # user doesn't exist
        flash_error("reset_password_error")
        
    return render_template('unregistered-forgotten-password.html', form = form)

@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    # Logout user if it's login
    if current_user.is_authenticated:
        logout_user()

    existing_user = User.query.filter_by(change_password_token=token).first()
    if existing_user is not None:
        form = ResetPasswordForm()
        if form.validate_on_submit():
            
            existing_user.change_password_token = None
            existing_user.set_password(form.password.data)
            db.session.commit() # set password an remove token

            # send email to confirm change
            email_task = TaskConfirmPasswordChangeEmail(name=existing_user.name,email=existing_user.email)
            task_manager.add_task(email_task)

            flash_info("change_password_successful")
            return redirect(url_for("auth_bp.login"))
        
        return render_template('unregistered-change-password.html', token = token, form = form)
    
    flash_error("change_password_error")
    return redirect(url_for("auth_bp.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Bypass if user is logged in
    if current_user.is_authenticated:
        return redirect(url_for("main_bp.init"))

    form = LoginForm()
    # Validate login attempt
    if form.validate_on_submit():
        lowercase_email = form.email.data.lower()

        existing_user = User.query.filter_by(email=lowercase_email).first()
        if existing_user and existing_user.check_password(password=form.password.data):
            
            logger.info(f"Login: {lowercase_email}")

            existing_user.change_password_token = None
            db.session.commit() # remove any existing token

            login_user(existing_user)
            
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main_bp.init"))

        flash_error("login_error")
        return redirect(url_for("auth_bp.login"))

    return render_template('unregistered-login.html', form = form)

@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None

@login_manager.unauthorized_handler
def unauthorized():
    flash_warning("unauthorized")
    # TODO: set next
    return redirect(url_for("auth_bp.login"))
