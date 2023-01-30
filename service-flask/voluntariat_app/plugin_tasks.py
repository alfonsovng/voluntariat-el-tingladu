import threading
import queue
import time

from .helper import logger

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
                except Exception as e:
                    logger.warning(f'Tasca amb error: {e}')
            except:
                time.sleep(self.pause_between_tasks)
