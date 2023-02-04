from .helper import logger

class UsherImpl:
    def get_description(self):
        raise NotImplementedError

    def get_rewards(self, user_id):
        raise NotImplementedError

    def get_meals(self, user_id):
        raise NotImplementedError

class Usher15Anniversary(UsherImpl):
    def get_description(self):
        return "15è aniversari del Tingladu el 13 de maig de 2023"

    def get_rewards(self, user_id):
        return []

    def get_meals(self, user_id):
        return []

class UsherManager:
    
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        dynamic_class_name = app.config.get('USHER_CLASS')
        self.usher_instance =  globals()[dynamic_class_name]()

        logger.info(f"USHER_CLASS = {dynamic_class_name}: {self.usher_instance.get_description()}")

