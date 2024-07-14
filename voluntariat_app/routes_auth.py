from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from . import login_manager, db, hashid_manager, task_manager, params_manager
from .forms_auth import LoginForm, SignUpForm, ForgottenPasswordForm, ResetPasswordForm, RegisterForm
from .models import User, UserRole, UserDiet, UserRewards, PartnerDNI
from .plugin_gmail import TaskSignUpEmail, TaskResetPasswordEmail, TaskConfirmPasswordChangeEmail
from .helper import flash_info, flash_warning, flash_error, logger, notify_identity_changed
from sqlalchemy import func

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
        email = form.email.data
        uppercase_dni = form.dni.data.upper()

        if User.query.filter(func.upper(User.email) == email.upper()).first():
            # user amb el mateix email existeix
            flash_warning("sign_up_error")
            return redirect(url_for("auth_bp.login"))
        
        existing_user_with_dni = User.query.filter(User.dni == uppercase_dni).first()
        if existing_user_with_dni:
            # dos casos, que ja estigui confirmat o no
            if existing_user_with_dni.confirmed:
                flash_warning("sign_up_error")
                return redirect(url_for("auth_bp.login"))
            else:
                # remove unconfirmed user with the same DNI
                db.session.delete(existing_user_with_dni) 
                db.session.commit()    
        
        role = UserRole.volunteer
        partner_dni = PartnerDNI.query.filter(PartnerDNI.dni == uppercase_dni).first()
        if partner_dni:
            # és un DNI de soci
            role = UserRole.partner

        if (role == UserRole.volunteer and not params_manager.allow_volunteers):
            flash_warning("no_partner")
            return redirect(url_for("main_bp.contact"))

        logger.info(f"Nou voluntari: {email}")

        user = User(
            name = "",
            surname = "",
            email = email,
            dni = uppercase_dni,
            phone = "",
            role = role,
            confirmed = False
        )
        # set a random password because it can't be null
        user.set_password(hashid_manager.create_password())
        db.session.add(user)
        db.session.commit()  # Create new user

        # create token with the user id
        token = hashid_manager.create_token(user.id)
        user.change_password_token = token
        db.session.add(user)
        
        db.session.commit() # guardem token
        
        # send email to end signup
        email_task = TaskSignUpEmail(email=email,token=token)
        task_manager.add_task(email_task)

        flash_info("sign_up_successful")
        return redirect(url_for("auth_bp.login"))
        
    return render_template('unregistered-sign-up.html', form = form)

@auth_bp.route("/forgotten-password", methods=["GET", "POST"])
def forgotten_password():
    # Bypass if user is logged in
    if current_user.is_authenticated:
        return redirect(url_for("main_bp.init"))

    form = ForgottenPasswordForm()
    # Validate sign up attempt
    if form.validate_on_submit():
        email = form.email.data

        existing_user = User.query.filter(func.upper(User.email) == email.upper()).first()
        if existing_user is not None:

            token = hashid_manager.create_token(existing_user.id)
            existing_user.change_password_token = token   
            db.session.commit()  # add token
           
            # send email to reset password
            email_task = TaskResetPasswordEmail(name=existing_user.name,email=email,token=token)
            task_manager.add_task(email_task)

            flash_info("reset_password_successful")
            return redirect(url_for("auth_bp.login"))

        # user doesn't exist
        flash_error("reset_password_error")
        
    return render_template('unregistered-forgotten-password.html', form = form)

@auth_bp.route("/register/<token>", methods=["GET", "POST"])
def register(token):
    # Logout user if it's login
    if current_user.is_authenticated:
        logout_user()

    existing_user = User.query.filter(User.change_password_token == token).first()
    if existing_user is not None:
        form = RegisterForm()
        form.set_email_confirmation(existing_user.email)

        if form.validate_on_submit():

            # Comprovo que l'email coincideix, si no, no deixo continuar
            if(form.email_confirmation.data.upper() != existing_user.email.upper()):
                flash_error("wrong_email_confirmation")
                return redirect(url_for("auth_bp.register", token=token))

            logger.info(f"Completant registre: {existing_user.email}")

            # afegeixo les dades del formulari a l'usuari
            form.populate_obj(existing_user)

            existing_user.confirmed = True
            existing_user.change_password_token = None
            existing_user.set_password(form.password.data)

            # guardo la informació de la seva dieta i les seves recompenses
            db.session.add(UserDiet(user_id = existing_user.id))
            db.session.add(UserRewards(user_id = existing_user.id))

            db.session.commit() # set password, remove token, dietes i recompenses

            # send email to confirm change
            email_task = TaskConfirmPasswordChangeEmail(name=existing_user.name,email=existing_user.email)
            task_manager.add_task(email_task)

            flash_info("change_password_successful")
            return redirect(url_for("auth_bp.login"))
        
        return render_template('unregistered-register.html', form = form)
    
    flash_error("wrong_token")
    return redirect(url_for("auth_bp.login"))

@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    # Logout user if it's login
    if current_user.is_authenticated:
        logout_user()

    existing_user = User.query.filter(User.change_password_token == token).first()
    if existing_user is not None:

        if(existing_user.confirmed == False):
            # és un usuari que no ha completat el registre
            return redirect(url_for("auth_bp.register", token=token))

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
        
        return render_template('unregistered-change-password.html', form = form)
    
    flash_error("wrong_token")
    return redirect(url_for("auth_bp.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Bypass if user is logged in
    if current_user.is_authenticated:
        return redirect(url_for("main_bp.init"))

    form = LoginForm()
    # Validate login attempt
    if form.validate_on_submit():
        email = form.email.data.lower()

        existing_user = User.query.filter(func.upper(User.email) == email.upper()).first()
        if existing_user and existing_user.check_password(password=form.password.data) and existing_user.confirmed:

            logger.info(f"Login: {email}")

            existing_user.change_password_token = None
            db.session.commit() # remove any existing token

            login_user(existing_user)

            # aquí s'actualitzen els rols que té l'usuari
            notify_identity_changed()
            
            next_page = request.args.get("next")

            if not params_manager.allow_modifications:
                flash_warning("read_only")

            return redirect(next_page or url_for("main_bp.init"))

        flash_error("login_error")
        return redirect(url_for("auth_bp.login"))
    
    if not params_manager.allow_volunteers:
        flash_info("no_partner")

    return render_template('unregistered-login.html', form = form)

@login_manager.user_loader
def load_user(user_id):
    if user_id is not None:
        return User.query.get(user_id)
    return None

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth_bp.login"))

@login_manager.unauthorized_handler
def unauthorized():
    flash_warning("unauthorized")
    # TODO: set next
    return redirect(url_for("auth_bp.login"))

@auth_bp.app_errorhandler(401)
def unauthorized(e):
    flash_warning("unauthorized")
    return redirect(url_for('auth_bp.login'))

@auth_bp.app_errorhandler(403)
def must_be_admin(e):
    flash_error("must_be_admin")
    return redirect(url_for('volunteer_bp.dashboard'))

@auth_bp.app_errorhandler(405)
def read_only(e):
    flash_error("read_only")
    return redirect(url_for('volunteer_bp.dashboard'))

