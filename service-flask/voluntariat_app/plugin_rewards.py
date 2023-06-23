from .helper import logger
from sqlalchemy import text

class RewardsImpl:
    def calculate_tickets(self, user, current_shifts):
        raise NotImplementedError

    def calculate_meals(self, user, current_shifts):
        raise NotImplementedError

    def _get_meal_id(self, db, name):
        id = db.session.execute(text(f"select id from meals where name = '{name}'")).one()[0] #it's a tuple
        logger.info(f"{self.__class__.__name__} - meal:{name} = {id}")
        return id

    def _get_ticket_id(self, db, name):
        id =  db.session.execute(text(f"select id from tickets where name = '{name}'")).one()[0] #it's a tuple
        logger.info(f"{self.__class__.__name__} - ticket:{name} = {id}")
        return id
    
    def _get_ticket_id(self, db, name):
        id =  db.session.execute(text(f"select id from tickets where name = '{name}'")).one()[0] #it's a tuple
        logger.info(f"{self.__class__.__name__} - ticket:{name} = {id}")
        return id
    
    def _get_task_id(self, db, name):
        id =  db.session.execute(text(f"select id from tasks where name = '{name}'")).one()[0] #it's a tuple
        logger.info(f"{self.__class__.__name__} - task:{name} = {id}")
        return id
    
    def _get_shift_id(self, db, task_id, name):
        id =  db.session.execute(text(f"select id from shifts where task_id = {task_id} and name = '{name}'")).one()[0] #it's a tuple
        logger.info(f"{self.__class__.__name__} - shift:{name} = {id}")
        return id

class Rewards15Edition(RewardsImpl):

    def __init__(self, app, db):
        with app.app_context():
            # àpats
            sopar_dijous_id = self._get_meal_id(db, "SOPAR DE DIJOUS")
            sopar_divendres_id = self._get_meal_id(db, "SOPAR DE DIVENDRES")
            sopar_dissabte_id = self._get_meal_id(db, "SOPAR DE DISSABTE")

            # entrades i acreditacions
            entrada_dijous_id = self._get_ticket_id(db, "ENTRADA DE DIJOUS")
            entrada_divendres_id = self._get_ticket_id(db, "ENTRADA DE DIVENDRES")
            entrada_dissabte_id = self._get_ticket_id(db, "ENTRADA DE DISSABTE")
            abonament_id = self._get_ticket_id(db, "ABONAMENT TRES DIES")
            voluntari_dijous_id = self._get_ticket_id(db, "VOLUNTARI DE DIJOUS")
            voluntari_divendres_id = self._get_ticket_id(db, "VOLUNTARI DE DIVENDRES")
            voluntari_dissabte_id = self._get_ticket_id(db, "VOLUNTARI DE DISSABTE")
            acreditacio_col_laborador_id = self._get_ticket_id(db, "ACREDITACIÓ COL·LABORADOR")
            acreditacio_globus_id = self._get_ticket_id(db, "ACREDITACIÓ GLOBUS")
            acreditacio_organitzacio_id = self._get_ticket_id(db, "ACREDITACIÓ ORGANITZACIÓ")
            acreditacio_treballador_id = self._get_ticket_id(db, "ACREDITACIÓ TREBALLADOR")
            acreditacio_punt_lila_i_food_truck_id = self._get_ticket_id(db, "ACREDITACIÓ PUNT LILA I FOOD TRUCK")

            # tasques
            barres_id = self._get_task_id(db, "BARRES")
            subcaps_barres_id = self._get_task_id(db, "SUBCAPS DE BARRES")
            entrades_id = self._get_task_id(db, "ENTRADES")
            marxandatge_id = self._get_task_id(db, "MARXANDATGE")
            cuina_id = self._get_task_id(db, "CUINA")
            globus_id = self._get_task_id(db, "GLOBUS")
            photocall_id = self._get_task_id(db, "PHOTOCALL")
            tresoreria_id = self._get_task_id(db, "TRESORERIA")
            muntatge_id = self._get_task_id(db, "MUNTATGE")
            suport_id = self._get_task_id(db, "SUPORT")
            organitzacio_id = self._get_task_id(db, "ORGANITZACIÓ")
            comunicacio_id = self._get_task_id(db, "COMUNICACIÓ")
            electrics_id = self._get_task_id(db, "ELÈCTRICS")
            so_id = self._get_task_id(db, "SO")
            seguretat_id = self._get_task_id(db, "SEGURETAT")
            punt_lila_i_food_truck_id = self._get_task_id(db, "PUNT LILA I FOOD TRUCK")

            self.tasques_amb_entrada_del_dia = frozenset([
                barres_id,
                subcaps_barres_id,
                entrades_id,
                marxandatge_id,
                cuina_id,
                globus_id,
                photocall_id,
                tresoreria_id,
                # muntatge_id,
                # suport_id,
                # organitzacio_id,
                # comunicacio_id,
                # electrics_id,
                # so_id,
                # seguretat_id,
                # punt_lila_i_food_truck_id,
            ])

            self.tasques_amb_voluntari_del_dia = frozenset([
                barres_id,
                subcaps_barres_id,
                entrades_id,
                marxandatge_id,
                # cuina_id,
                # globus_id,
                photocall_id,
                # tresoreria_id,
                # muntatge_id,
                # suport_id,
                # organitzacio_id,
                # comunicacio_id,
                # electrics_id,
                # so_id,
                # seguretat_id,
                # punt_lila_i_food_truck_id,
            ])

            self.tasques_amb_sopar_del_dia = frozenset([
                barres_id,
                subcaps_barres_id,
                entrades_id,
                marxandatge_id,
                cuina_id,
                globus_id,
                photocall_id,
                tresoreria_id,
                # muntatge_id,
                # suport_id,
                # organitzacio_id,
                # comunicacio_id,
                # electrics_id,
                # so_id,
                # seguretat_id,
                # punt_lila_i_food_truck_id,
            ])

            self.tasques_amb_tots_els_sopars = frozenset([
                # barres_id,
                # subcaps_barres_id,
                # entrades_id,
                # marxandatge_id,
                # cuina_id,
                # globus_id,
                # photocall_id,
                # tresoreria_id,
                # muntatge_id,
                suport_id,
                organitzacio_id,
                comunicacio_id,
                # electrics_id,
                so_id,
                seguretat_id,
                # punt_lila_i_food_truck_id,
            ])

            self.acreditacions = [
                [acreditacio_col_laborador_id, frozenset([
                    # barres_id,
                    # subcaps_barres_id,
                    # entrades_id,
                    # marxandatge_id,
                    cuina_id,
                    # globus_id,
                    # photocall_id,
                    tresoreria_id,
                    # muntatge_id,
                    # suport_id,
                    # organitzacio_id,
                    comunicacio_id,
                    # electrics_id,
                    # so_id,
                    # seguretat_id,
                    # punt_lila_i_food_truck_id,
                ])],
                [acreditacio_globus_id, frozenset([
                    # barres_id,
                    # subcaps_barres_id,
                    # entrades_id,
                    # marxandatge_id,
                    # cuina_id,
                    globus_id,
                    # photocall_id,
                    # tresoreria_id,
                    # muntatge_id,
                    # suport_id,
                    # organitzacio_id,
                    # comunicacio_id,
                    # electrics_id,
                    # so_id,
                    # seguretat_id,
                    # punt_lila_i_food_truck_id,
                ])],
                [acreditacio_organitzacio_id, frozenset([
                    # barres_id,
                    # subcaps_barres_id,
                    # entrades_id,
                    # marxandatge_id,
                    # cuina_id,
                    # globus_id,
                    # photocall_id,
                    # tresoreria_id,
                    # muntatge_id,
                    # suport_id,
                    organitzacio_id,
                    # comunicacio_id,
                    # electrics_id,
                    # so_id,
                    # seguretat_id,
                    # punt_lila_i_food_truck_id,
                ])],
                [acreditacio_treballador_id, frozenset([
                    # barres_id,
                    # subcaps_barres_id,
                    # entrades_id,
                    # marxandatge_id,
                    # cuina_id,
                    # globus_id,
                    # photocall_id,
                    # tresoreria_id,
                    # muntatge_id,
                    # suport_id,
                    # organitzacio_id,
                    # comunicacio_id,
                    # electrics_id,
                    so_id,
                    seguretat_id,
                    # punt_lila_i_food_truck_id,
                ])],
                [acreditacio_punt_lila_i_food_truck_id, frozenset([
                    # barres_id,
                    # subcaps_barres_id,
                    # entrades_id,
                    # marxandatge_id,
                    # cuina_id,
                    # globus_id,
                    # photocall_id,
                    # tresoreria_id,
                    # muntatge_id,
                    # suport_id,
                    # organitzacio_id,
                    # comunicacio_id,
                    # electrics_id,
                    # so_id,
                    # seguretat_id,
                    punt_lila_i_food_truck_id,
                ])],
            ]

    def calculate_tickets(self, user, current_shifts):
        return []
        # from .models import UserTicket

        # if len(current_shifts) == 0:
        #     return []
        
        # # amb un diccionari evito tickets duplicats
        # tickets_assigned = {}
        # for (t, s, us) in current_shifts:
        #     # busco per tasques
        #     for (ticket_id, task_id_set) in self.tickets_by_task:
        #         if t.id in task_id_set:
        #             ticket = UserTicket(
        #                 user_id = user.id,
        #                 ticket_id = ticket_id,
        #                 selected = True
        #             )
        #             tickets_assigned[ticket_id] = ticket
        #     # i per torns
        #     for (ticket_id, shift_id_set) in self.tickets_by_shift:
        #         if s.id in shift_id_set:
        #             ticket = UserTicket(
        #                 user_id = user.id,
        #                 ticket_id = ticket_id,
        #                 selected = True
        #             )
        #             tickets_assigned[ticket_id] = ticket

        # return tickets_assigned.values()

    def calculate_meals(self, user, current_shifts):
        return []
        # from .models import UserMeal

        # if len(current_shifts) == 0:
        #     return []

        # # amb un diccionari evito àpats duplicats
        # meals_assigned = {}
        # for (t, s, us) in current_shifts:
        #     for (meal_id, task_id_set) in self.meals_by_task:
        #         if t.id in task_id_set:
        #             meal = UserMeal(
        #                 user_id = user.id,
        #                 meal_id = meal_id,
        #                 selected = True
        #             )
        #             meals_assigned[meal_id] = meal

        # return meals_assigned.values()

class RewardsManager:
    
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app, db):
        dynamic_class_name = app.config.get('REWARDS_CLASS')
        logger.info(f"REWARDS_CLASS = {dynamic_class_name}")
        self.rewards_instance =  globals()[dynamic_class_name](app, db)

    def update_all_rewards(self):
        from .models import User

        users = User.query.all()
        for user in users:
            self.update_rewards(user)

    def update_rewards(self, user):
        # miro quins torns fa l'usuari
        current_shifts = self.__get_current_shifts(user.id)

        logger.info(f"Update rewards of {user.full_name}")

        # actualitzo tickets, acreditacions i àpats
        self.__update_tickets(user, current_shifts)
        self.__update_meals(user, current_shifts)

        # actualitzo el last_change_at de l'usuari
        self.__update_user(user)

    def __get_current_shifts(self, user_id):
        from .models import UserShift, Shift, Task
        from . import db

        return db.session.query(Task, Shift, UserShift).join(Shift, Task.id == Shift.task_id).join(UserShift).filter(UserShift.user_id == user_id).all()

    def __update_tickets(self, user, current_shifts):
        from .models import UserTicket
        from . import db

        current_tickets = UserTicket.query.filter(UserTicket.user_id == user.id).all()
        new_tickets = self.rewards_instance.calculate_tickets(
            user = user,
            current_shifts = current_shifts
        )

        merged_tickets = self.__merge_tickets(
            current_tickets = current_tickets,
            new_tickets = new_tickets
        )

        UserTicket.query.filter(UserTicket.user_id == user.id).delete()
        db.session.add_all(merged_tickets)

    def __merge_tickets(self, current_tickets, new_tickets):
        for ticket in new_tickets:
            existing_ticket = self.__get_first_with_filter(lambda t:t.ticket_id == ticket.ticket_id, current_tickets)
            if existing_ticket:
                ticket.selected = existing_ticket.selected

        return new_tickets

    def __update_meals(self, user, current_shifts):
        from .models import UserMeal
        from . import db

        current_meals = UserMeal.query.filter(UserMeal.user_id == user.id).all()
        new_meals = self.rewards_instance.calculate_meals(
            user = user,
            current_shifts = current_shifts
        )

        merged_meals = self.__merge_meals(
            current_meals = current_meals,
            new_meals = new_meals
        )
        UserMeal.query.filter(UserMeal.user_id == user.id).delete()
        db.session.add_all(merged_meals)

    def __merge_meals(self, current_meals, new_meals):
        for meal in new_meals:
            existing_meal = self.__get_first_with_filter(lambda m:m.meal_id == meal.meal_id, current_meals)
            if existing_meal:
                meal.selected = existing_meal.selected
                meal.comments = existing_meal.comments

        return new_meals

    def __get_first_with_filter(self, lambda_filter, list):
        filtered_list = filter(lambda_filter, list)
        return next(iter(filtered_list), None)
    
    def __update_user(self, user):
        from . import db
        from sqlalchemy.sql import func

        user.last_shift_change_at = func.now()
        db.session.add(user)

    def calculate_cash(self, user):
        cash = 0
        cash_details = list()

        current_shifts = self.__get_current_shifts(user.id)
        for (t, s, us) in current_shifts:
            if s.reward > 0:
                if s.assignations: # no es buit, és a dir, hi ha opcions
                    zero_assignations = True
                    for (name, assigned) in zip(s.assignations, us.shift_assignations):
                        if assigned:
                            cash_details.append((f"{t.name} - {s.name} - {name}", s.reward))
                            cash += s.reward
                            zero_assignations = False
                        
                    if zero_assignations:
                        cash_details.append((f"{t.name} - {s.name}", None))
                else:
                    cash_details.append((f"{t.name} - {s.name}", s.reward))
                    cash += s.reward

        return (cash, cash_details)