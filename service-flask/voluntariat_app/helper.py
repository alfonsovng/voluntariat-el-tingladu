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
def flash_info(message:str) -> None:
    flash(message=message, category='alert-info')

def flash_warning(message:str) -> None:
    flash(message=message, category='alert-warning')

def flash_error(message:str) -> None:
    flash(message=message, category='alert-error')


#
# Funció per carregar les dades d'un voluntari. Controla si l'usuari és un
# administrador, pq hi ha dades que si pot veure un administrador, i d'altres no,
# com un password.
#
def load_volunteer(current_user,volunteer_hashid,allow_all_admins=True):
    from . import hashid_manager
    volunteer_id = hashid_manager.get_id_from_hashid(volunteer_hashid)

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