import threading
import queue
import time

class TaskManager:

    run_worker = True
    pause_between_tasks = 30
    task_queue = queue.SimpleQueue()

    def __init__(self, app=None):
        self.hashids_generator = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):     
        pause_between_tasks = app.config.get('TASKS_PAUSE', TaskManager.pause_between_tasks)
        TaskManager.pause_between_tasks = pause_between_tasks

        # Turn-on the worker thread.
        threading.Thread(target=TaskManager.worker, name='TaskManagerThread', daemon=True).start()

    def add_task(self, task):
        TaskManager.task_queue.put_nowait(task)
        print(f'Tasks in task_queue: {TaskManager.task_queue.qsize()}')

    def worker():
        while True:
            try:
                task = TaskManager.task_queue.get_nowait()
                try:
                    if task is not None:
                        task.do_it()
                except Exception as e:
                    print(f'Task error! {e}')
            except:
                print(f'No task to do... waiting {TaskManager.pause_between_tasks}')
                time.sleep(TaskManager.pause_between_tasks)

