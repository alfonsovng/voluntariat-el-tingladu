from .helper import logger

class RewardsImpl:
    def calculate_tickets(self, user_id, current_shifts):
        raise NotImplementedError

    def calculate_meals(self, user_id, current_shifts):
        raise NotImplementedError

    def _get_meal_id(self, db, code):
        id = db.session.execute(f"select id from meals where code = '{code}'").one()[0] #it's a tuple
        logger.info(f"{self.__class__.__name__} - meal:{code} = {id}")
        return id

    def _get_ticket_id(self, db, code):
        id =  db.session.execute(f"select id from tickets where code = '{code}'").one()[0] #it's a tuple
        logger.info(f"{self.__class__.__name__} - ticket:{code} = {id}")
        return id

class Rewards15Anniversary(RewardsImpl):

    def __init__(self, app, db):
        with app.app_context():
            self.sopar_15_aniversari_id = self._get_meal_id(db, "sopar_15_aniversari")
            self.entrada_15_aniversari_id = self._get_ticket_id(db, "entrada_15_aniversari")

    def calculate_tickets(self, user_id, current_shifts):
        from .models import UserTicket

        if len(current_shifts) == 0:
            return []

        # Entrada del dia per qualsevol que faci tasques aquest dia.
        # No es pot renunciar.
        ticket = UserTicket(
            user_id = user_id,
            options = [self.entrada_15_aniversari_id],
            selected = self.entrada_15_aniversari_id
        )

        return [ticket]

    def calculate_meals(self, user_id, current_shifts):
        from .models import UserMeal

        if len(current_shifts) == 0:
            return []

        # Sopar del dia del concert per qualsevol que faci tasques. 
        # Es pot renunciar. No surt seleccionat per defecte
        meal = UserMeal(
            user_id = user_id,
            options = [0,self.sopar_15_aniversari_id],
            selected = 0
        )

        return [meal]

class RewardsManager:
    
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app, db):
        dynamic_class_name = app.config.get('REWARDS_CLASS')
        logger.info(f"REWARDS_CLASS = {dynamic_class_name}")
        self.rewards_instance =  globals()[dynamic_class_name](app, db)

    def update_tickets(self, user_id, current_shifts):
        from .models import UserTicket
        from . import db

        current_tickets = UserTicket.query.filter(UserTicket.user_id == user_id).all()
        new_tickets = self.rewards_instance.calculate_tickets(
            user_id = user_id,
            current_shifts = current_shifts
        )

        merged_tickets = self.merge(
            current_stuff = current_tickets,
            new_stuff = new_tickets
        )

        UserTicket.query.filter(UserTicket.user_id == user_id).delete()
        db.session.add_all(merged_tickets)

    def update_meals(self, user_id, current_shifts):
        from .models import UserMeal
        from . import db

        current_meals = UserMeal.query.filter(UserMeal.user_id == user_id).all()
        new_meals = self.rewards_instance.calculate_meals(
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