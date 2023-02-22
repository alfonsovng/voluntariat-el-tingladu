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
    
    def _get_accreditation_id(self, db, code):
        id =  db.session.execute(f"select id from accreditations where code = '{code}'").one()[0] #it's a tuple
        logger.info(f"{self.__class__.__name__} - accreditation:{code} = {id}")
        return id

class Rewards15Anniversary(RewardsImpl):

    def __init__(self, app, db):
        with app.app_context():
            # àpats
            self.dinar_15_aniversari_id = self._get_meal_id(db, "dinar_15_aniversari")
            self.sopar_15_aniversari_id = self._get_meal_id(db, "sopar_15_aniversari")

            # entrades
            self.entrada_15_aniversari_id = self._get_ticket_id(db, "entrada_15_aniversari")

            # acreditacions
            self.pulsera_voluntari_id = self._get_accreditation_id(db, "pulsera_voluntari")
            self.acreditacio_globus_id = self._get_accreditation_id(db, "acreditacio_globus")
            self.acreditacio_org_id = self._get_accreditation_id(db, "acreditacio_org")

    def calculate_tickets(self, user_id, current_shifts):
        from .models import UserTicket

        if len(current_shifts) == 0:
            return []

        # Entrada del dia per qualsevol que faci tasques aquest dia.
        # No es pot renunciar.
        ticket = UserTicket(
            user_id = user_id,
            ticket_id = self.entrada_15_aniversari_id,
            selected = True
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
            meal_id = self.sopar_15_aniversari_id,
            selected = False
        )

        return [meal]

    def calculate_accreditations(self, user_id, current_shifts):
        # TODO
        return []

class RewardsManager:
    
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app, db):
        dynamic_class_name = app.config.get('REWARDS_CLASS')
        logger.info(f"REWARDS_CLASS = {dynamic_class_name}")
        self.rewards_instance =  globals()[dynamic_class_name](app, db)

    def update_rewards(self, user_id):
        from .models import UserShift

        # miro quins torns fa l'usuari
        current_shifts = UserShift.query.filter_by(user_id = user_id).all()

        # actualitzo tickets, àpats i acreditacions
        self.__update_tickets(user_id, current_shifts)
        self.__update_meals(user_id, current_shifts)
        self.__update_accreditations(user_id, current_shifts)

    def __update_tickets(self, user_id, current_shifts):
        from .models import UserTicket
        from . import db

        current_tickets = UserTicket.query.filter(UserTicket.user_id == user_id).all()
        new_tickets = self.rewards_instance.calculate_tickets(
            user_id = user_id,
            current_shifts = current_shifts
        )

        merged_tickets = self.__merge_tickets(
            current_tickets = current_tickets,
            new_tickets = new_tickets
        )

        UserTicket.query.filter(UserTicket.user_id == user_id).delete()
        db.session.add_all(merged_tickets)

    def __merge_tickets(self, current_tickets, new_tickets):
        for ticket in new_tickets:
            existing_ticket = self.__get_first_with_filter(lambda t:t.ticket_id == ticket.ticket_id, current_tickets)
            if existing_ticket:
                ticket.selected = existing_ticket.selected
                ticket.comments = existing_ticket.comments

        return new_tickets

    def __update_meals(self, user_id, current_shifts):
        from .models import UserMeal
        from . import db

        current_meals = UserMeal.query.filter(UserMeal.user_id == user_id).all()
        new_meals = self.rewards_instance.calculate_meals(
            user_id = user_id,
            current_shifts = current_shifts
        )

        merged_meals = self.__merge_meals(
            current_meals = current_meals,
            new_meals = new_meals
        )
        UserMeal.query.filter(UserMeal.user_id == user_id).delete()
        db.session.add_all(merged_meals)

    def __merge_meals(self, current_meals, new_meals):
        for meal in new_meals:
            existing_meal = self.__get_first_with_filter(lambda m:m.meal_id == meal.meal_id, current_meals)
            if existing_meal:
                meal.selected = existing_meal.selected
                meal.comments = existing_meal.comments

        return new_meals

    def __update_accreditations(self, user_id, current_shifts):
        from .models import UserAccreditation
        from . import db

        current_accreditations = UserAccreditation.query.filter(UserAccreditation.user_id == user_id).all()
        new_accreditations = self.rewards_instance.calculate_accreditations(
            user_id = user_id,
            current_shifts = current_shifts
        )

        merged_accreditations = self.__merge_accreditations(
            current_accreditations = current_accreditations,
            new_accreditations = new_accreditations
        )
        UserAccreditation.query.filter(UserAccreditation.user_id == user_id).delete()
        db.session.add_all(merged_accreditations)

    def __merge_accreditations(self, current_accreditations, new_accreditations):
        # no cal fer res, es poden esborrar les que hi havia i inserir-les de nou
        return new_accreditations

    def __get_first_with_filter(self, lambda_filter, list):
        filtered_list = filter(lambda_filter, list)
        return next(iter(filtered_list), None)

    def calculate_cash(self, user_id):
        from .models import UserShift, Shift, Task
        from . import db

        shifts = db.session.query(Task, Shift, UserShift).join(Shift, Task.id == Shift.task_id).join(UserShift).filter(UserShift.user_id == user_id).all()
        cash = 0
        cash_details = list()
        for (t, s, us) in shifts:
            if s.reward > 0:
                if s.assignations: # no es buit, és a dir, hi ha opcions
                    zero_assignations = True
                    for (name, assigned) in zip(s.assignations, us.shift_assignations):
                        if assigned:
                            cash_details.append(f"{t.name} - {s.name} - {name}: {s.reward} €")
                            cash += s.reward
                            zero_assignations = False
                        
                    if zero_assignations:
                        cash_details.append(f"{t.name} - {s.name}: pendent d'assignació")
                else:
                    cash_details.append(f"{t.name} - {s.name}: {s.reward} €")
                    cash += s.reward

        return (cash, cash_details)