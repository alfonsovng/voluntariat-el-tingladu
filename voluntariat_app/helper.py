#
# Logger
# 
def __create_logger():
    import logging
    from flask.logging import default_handler
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(default_handler)
    return logger

logger = __create_logger()


#
# Task interface
# totes les tasques que volem fer de manera asíncrona, com enviar un email,
# s'han definir implementant aquesta interfície i fent servir el plugin_tasks
#
class Task:
    def __init__(self):
        pass

    def do_it(self):
        pass


#
# Missatges de flash amb la categoria fixa
# Category values from https://www.w3schools.com/bootstrap4/bootstrap_alerts.asp
#
from flask import flash
def flash_info(message_id:str) -> None:
    message = labels.get(message_id)
    flash(message=message, category='alert-secondary')

def flash_warning(message_id:str) -> None:
    message = labels.get(message_id)
    flash(message=message, category='alert-warning')

def flash_error(message_id:str) -> None:
    message = labels.get(message_id)
    flash(message=message, category='alert-error')


#
# Funció per carregar les dades d'un voluntari. Controla si l'usuari és un
# administrador, pq hi ha dades que si pot veure un administrador, i d'altres no,
# com un password.
#
def load_volunteer(current_user,volunteer_hashid,allow_all_admins=True):
    from . import hashid_manager
    volunteer_id = hashid_manager.get_user_id_from_hashid(volunteer_hashid)

    if volunteer_id is None:
        volunteer = None
    elif current_user.id == volunteer_id:
        volunteer = current_user
    elif allow_all_admins and current_user.is_admin:
        from .models import User

        # if admin, can see other volunteers data
        volunteer = User.query.get(volunteer_id)
    else:
        volunteer = None

    return volunteer


#
# Resum ràpid dels torns, àpats i entrades que té un usuari
#
def get_shifts_meals_and_tickets(user_id):
    from . import db
    from sqlalchemy import text

    shifts = get_shifts(user_id)

    meals = [m for m in db.session.execute(text(f"""select m.name 
        from meals as m 
        join user_meals as um on m.id=um.meal_id 
        where um.selected and um.user_id = {user_id}""")).scalars()]
    tickets = [t for t in db.session.execute(text(f"""select t.name 
        from tickets as t 
        join user_tickets as ut on t.id=ut.ticket_id 
        where ut.user_id = {user_id}""")).scalars()]

    return (shifts, meals, tickets)

def get_shifts(user_id):
    from . import db
    from sqlalchemy import text

    # reunió informativa també com a torn
    label_informative_meeting = labels.get("informative_meeting")

    shifts = [s for s in db.session.execute(text(f"""
        select -1, '{label_informative_meeting}: ' || informative_meeting from users 
        where id = {user_id} and informative_meeting!=''                                         
        union                                                    
        select s.id, t.name || ': ' || s.description || case when d.assignations is NULL then '' else ' [' || d.assignations || ']' end
        from tasks as t 
        join shifts as s on t.id = s.task_id 
        join user_shifts as us on us.shift_id = s.id
        left join (
            select a.shift_id, array_to_string(array_agg(a.name),' + ') as assignations 
            from (
                select s.id as shift_id, unnest(s.assignations) as name, unnest(us.shift_assignations) as assignation 
                from shifts as s join user_shifts as us on us.shift_id = s.id where us.user_id = {user_id}
            ) as a
            where a.assignation group by a.shift_id
        ) as d on d.shift_id = s.id
        where us.user_id = {user_id}
        order by 1""")).scalars()]
    
    return shifts

#
# Elimina els espais en blanc, controlant que no sigui None
# 
def trim(s):
    if s is None:
        return None
    return s.strip()


# 
# Retorna un timestamp
#
def get_timestamp():
    from datetime import datetime
    import time
    return datetime.fromtimestamp(time.time()).strftime("%Y%m%d%H%M%S")


#
# Labels
#
import configparser
import os

class LabelsManager:
    
    def __init__(self):
        self.config = configparser.ConfigParser()

        full_path = os.path.realpath(__file__)
        current_directory = os.path.dirname(full_path)

        self.config.read(current_directory + "/labels/texts.ini", encoding="utf-8")
        self.section = "CA" # TODO: fer multilanguage

    def get(self, key):
        value = self.config[self.section].get(key)
        if value is None:
            logger.warn(f"No s'ha trobat el label: {key}")
            return key
        return value

labels = LabelsManager()


#
# ROLE
#
from flask_principal import identity_loaded, identity_changed, ActionNeed, Permission, Identity, AnonymousIdentity

__superadmin_action_need = ActionNeed('superadmin')
__admin_action_need = ActionNeed('admin')
__edit_action_need = ActionNeed('edit')
__view_action_need = ActionNeed('view')
__login_action_need = ActionNeed('login')

__require_superadmin = Permission(__superadmin_action_need)
def require_superadmin():
    return __require_superadmin.require(http_exception=403)

__require_admin = Permission(__admin_action_need)
def require_admin():
    return __require_admin.require(http_exception=403)

__require_edit = Permission(__edit_action_need)
def is_read_only():
    return not __require_edit.can()

__require_view = Permission(__view_action_need)
def require_view():
    return __require_view.require(http_exception=405)

__require_login = Permission(__login_action_need)
def require_login():
    return __require_login.require(http_exception=401)

@identity_loaded.connect
def on_identity_loaded(sender, identity):
    from .models import UserRole
    from flask_login import current_user

    identity.user = current_user
    if hasattr(current_user, 'role'):
        from . import params_manager

        if current_user.role == UserRole.superadmin:
            identity.provides.add(__superadmin_action_need)
            identity.provides.add(__admin_action_need)
            identity.provides.add(__edit_action_need)
            identity.provides.add(__view_action_need)
            identity.provides.add(__login_action_need)
        elif current_user.role == UserRole.admin:
            identity.provides.add(__admin_action_need)
            identity.provides.add(__edit_action_need)
            identity.provides.add(__view_action_need)
            identity.provides.add(__login_action_need)
        elif current_user.role == UserRole.partner:
            identity.provides.add(__view_action_need)
            identity.provides.add(__login_action_need)
            if (params_manager.allow_modifications):
                identity.provides.add(__edit_action_need)
        elif current_user.role == UserRole.volunteer:
            identity.provides.add(__login_action_need)
            if(params_manager.allow_volunteers):
                if (params_manager.allow_modifications):
                    identity.provides.add(__edit_action_need)
                identity.provides.add(__view_action_need)
            else:
                logger.warn(f"Volunteers are not allowed: {current_user.email}")

def notify_identity_changed():
    from flask import current_app
    from flask_login import current_user

    if hasattr(current_user, 'id'):
        identity = Identity(current_user.id)
    else:
        identity = AnonymousIdentity()
    
    identity_changed.send(current_app._get_current_object(), identity = identity)