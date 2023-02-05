from .helper import logger

class UsherImpl:
    def get_description(self):
        raise NotImplementedError

    def calculate_rewards(self, user_id, current_shifts):
        raise NotImplementedError

    def calculate_meals(self, user_id, current_shifts):
        raise NotImplementedError

class Usher15Anniversary(UsherImpl):
    def get_description(self):
        return "15è aniversari del Tingladu el 13 de maig de 2023"

    def calculate_rewards(self, user_id, current_shifts):
        from .models import UserReward

        if len(current_shifts) == 0:
            return []

        # Entrada del dia per qualsevol que faci tasques aquest dia.
        # No es pot renunciar.
        reward = UserReward(
            user_id = user_id,
            options = [1],
            selected = 1
        )

        return [reward]

    def calculate_meals(self, user_id, current_shifts):
        from .models import UserMeal

        if len(current_shifts) == 0:
            return []

        # Sopar del dia del concert per qualsevol que faci tasques. 
        # Es pot renunciar. No surt seleccionat per defecte
        meal = UserMeal(
            user_id = user_id,
            options = [0,1],
            selected = 0
        )

        return [meal]

class UsherManager:
    
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        dynamic_class_name = app.config.get('USHER_CLASS')
        self.usher_instance =  globals()[dynamic_class_name]()

        logger.info(f"USHER_CLASS = {dynamic_class_name}: {self.usher_instance.get_description()}")

    def update_rewards(self, user_id, current_shifts):
        from .models import UserReward
        from . import db

        current_rewards = UserReward.query.filter(UserReward.user_id == user_id).all()
        new_rewards = self.usher_instance.calculate_rewards(
            user_id = user_id,
            current_shifts = current_shifts
        )

        merged_rewards = self.merge(
            current_stuff = current_rewards,
            new_stuff = new_rewards
        )

        UserReward.query.filter(UserReward.user_id == user_id).delete()
        db.session.add_all(merged_rewards)

    def update_meals(self, user_id, current_shifts):
        from .models import UserMeal
        from . import db

        current_meals = UserMeal.query.filter(UserMeal.user_id == user_id).all()
        new_meals = self.usher_instance.calculate_meals(
            user_id = user_id,
            current_shifts = current_shifts
        )

        merged_meals = self.merge(
            current_stuff = current_meals,
            new_stuff = new_meals
        )
        UserMeal.query.filter(UserMeal.user_id == user_id).delete()
        db.session.add_all(merged_meals)

    def merge(self, current_stuff, new_stuff):
        # TODO
        return new_stuff