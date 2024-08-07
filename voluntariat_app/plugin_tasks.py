import threading
import queue
import time

from .helper import logger, Task

class TaskManager:
    
    def __init__(self, app=None):
        self.hashids_generator = None
        self.task_queue = queue.SimpleQueue()
        self.pause_between_tasks = 30
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        pause_between_tasks = app.config.get('TASKS_PAUSE', self.pause_between_tasks)
        self.pause_between_tasks = pause_between_tasks
        self.shifts_email_task = ShiftsEmail(app, self.task_queue)

        # Turn-on the worker thread
        threading.Thread(target=self.worker, name='TaskManagerThread', daemon=True).start()

    def add_task(self, task):
        self.task_queue.put_nowait(task)
        logger.info(f"Afegida una nova tasca, ara n'hi ha {self.task_queue.qsize()}")

    def worker(self):
        while True:
            try:
                task = self.task_queue.get_nowait()
                try:
                    if task is not None:
                        logger.info("Executant una tasca...")
                        task.do_it()
                        time.sleep(5) # FIXME: 5 segons entre tasca i tasca
                except Exception as e:
                    logger.warning(f'Tasca amb error: {e}')
            except:
                time.sleep(self.pause_between_tasks)
                self.add_task(self.shifts_email_task)

class ShiftsEmail(Task):

    def __init__(self, app, task_queue):
        super().__init__()
        self.__app = app
        self.__task_queue = task_queue

    def do_it(self):
        from datetime import timedelta
        from sqlalchemy import update
        from sqlalchemy.sql import func
        from sqlalchemy.orm import Session
        from .models import User, UserRole
        from . import db, helper
        from .plugin_gmail import TaskProvisionalShiftsEmail

        with self.__app.app_context():

            logger.info("Comprovant si hi ha usuaris als que notificar els seus torns")

            # que tan sols envii 10 mails a la vegada
            users = User.query.filter(User.role != UserRole.worker).filter(
                (User.last_shift_change_at+timedelta(hours=2)) < func.now()
            ).order_by(User.id.asc()).limit(10).all()

            for user_with_changes in users:

                logger.info(f"Comprovant usuari {user_with_changes}...")

                with Session(db.engine) as session: # creo una sessió exclusiva
                    with session.begin():
                        result = session.execute(
                            update(User)
                                .values(last_shift_change_at=None)
                                .where(User.last_shift_change_at == user_with_changes.last_shift_change_at)
                                .where(User.id == user_with_changes.id)
                        )
                        # m'asseguro que s'ha fet l'update, per a evitar molts emails en un entorn multithread
                        if result.rowcount == 1:
                            shifts = helper.get_shifts(user_with_changes.id)

                            if len(shifts) > 0:
                                # envio un email dels torns apuntats!
                                logger.info(f"Email amb els torns a l'usuari {user_with_changes}")
                                self.__task_queue.put_nowait(TaskProvisionalShiftsEmail(user_with_changes, shifts))
