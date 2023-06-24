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

    shifts = [s for s in db.session.execute(text(f"""select t.name || ': ' || s.day || ', ' || s.description
        from tasks as t 
        join shifts as s on t.id = s.task_id 
        join user_shifts as us on us.shift_id = s.id 
        where us.user_id = {user_id}""")).scalars()]
    meals = [m for m in db.session.execute(text(f"""select m.name 
        from meals as m 
        join user_meals as um on m.id=um.meal_id 
        where um.selected and um.user_id = {user_id}""")).scalars()]
    tickets = [t for t in db.session.execute(text(f"""select t.name 
        from tickets as t 
        join user_tickets as ut on t.id=ut.ticket_id 
        where ut.user_id = {user_id}""")).scalars()]

    return (shifts, meals, tickets)


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

        self.config.read(current_directory + "/labels/texts.ini")
        self.section = "CA" # TODO: fer multilanguage

    def get(self, key):
        value = self.config[self.section].get(key)
        if value is None:
            logger.warn(f"No s'ha trobat el label: {key}")
            return key
        return value

labels = LabelsManager()