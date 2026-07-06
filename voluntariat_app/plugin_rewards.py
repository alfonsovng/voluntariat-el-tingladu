from .helper import logger, labels
from sqlalchemy import text

class RewardsImpl:
    def calculate_tickets(self, user, current_shifts):
        raise NotImplementedError

    def calculate_meals(self, user, current_shifts):
        raise NotImplementedError
    
    def calculate_cash(self, current_tickets, current_shifts):
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

class Rewards18Edition(RewardsImpl):

    def __init__(self, app, db):
        with app.app_context():
            # dies
            self.dijous = "23-07 DIJOUS"
            self.divendres = "24-07 DIVENDRES"
            self.dissabte = "25-07 DISSABTE"

            # tasques
            entrades_id = self._get_task_id(db, "ENTRADES")
            barres_id = self._get_task_id(db, "BARRES")
            barres_restringit_id = self._get_task_id(db, "BARRES RESTRINGIT")
            barres_collectiu_torn_id = self._get_task_id(db, "BARRES COL·LECTIU")
            subcaps_barres_id = self._get_task_id(db, "SUBCAPS DE BARRES")
            marxandatge_id = self._get_task_id(db, "MARXANDATGE")
            photocall_id = self._get_task_id(db, "PHOTOCALL")
            suport_collectius_id = self._get_task_id(db, "SUPORT COL·LECTIUS")
            muntatge_id = self._get_task_id(db, "MUNTATGE")
            cuina_id = self._get_task_id(db, "CUINA")
            globus_id = self._get_task_id(db, "GLOBUS")    
            tresoreria_id = self._get_task_id(db, "TRESORERIA")
            comunicacio_id = self._get_task_id(db, "COMUNICACIÓ")
            collaboracio_id = self._get_task_id(db, "COL·LABORACIÓ")
            organitzacio_id = self._get_task_id(db, "ORGANITZACIÓ")
            professional_id = self._get_task_id(db, "PROFESSIONAL")

            # àpats
            sopar_dijous_id = self._get_meal_id(db, "SOPAR DE DIJOUS")
            sopar_divendres_id = self._get_meal_id(db, "SOPAR DE DIVENDRES")
            sopar_dissabte_id = self._get_meal_id(db, "SOPAR DE DISSABTE")
            
            sopar_del_dia_que_ajuden = {
                self.dijous: [sopar_dijous_id],
                self.divendres: [sopar_divendres_id],
                self.dissabte: [sopar_dissabte_id],
            }

            tots_els_sopars = [sopar_dijous_id, sopar_divendres_id, sopar_dissabte_id]

            self.assignacio_apats = {
                entrades_id: sopar_del_dia_que_ajuden,
                barres_id: sopar_del_dia_que_ajuden,
                barres_restringit_id: sopar_del_dia_que_ajuden,
                barres_collectiu_torn_id: sopar_del_dia_que_ajuden,
                subcaps_barres_id: sopar_del_dia_que_ajuden,
                marxandatge_id: sopar_del_dia_que_ajuden,
                photocall_id: sopar_del_dia_que_ajuden,
                suport_collectius_id: sopar_del_dia_que_ajuden,
                muntatge_id: [],
                cuina_id: sopar_del_dia_que_ajuden,
                globus_id: sopar_del_dia_que_ajuden,
                tresoreria_id: sopar_del_dia_que_ajuden,
                comunicacio_id: sopar_del_dia_que_ajuden,
                collaboracio_id: tots_els_sopars,
                organitzacio_id: tots_els_sopars,
                professional_id: sopar_del_dia_que_ajuden,
            }

            # entrades i acreditacions
            entrada_dijous_id = self._get_ticket_id(db, "ENTRADA DE DIJOUS")
            entrada_divendres_id = self._get_ticket_id(db, "ENTRADA DE DIVENDRES")
            entrada_dissabte_id = self._get_ticket_id(db, "ENTRADA DE DISSABTE")
            abonament_id = self._get_ticket_id(db, "ABONAMENT 3 DIES")
            voluntari_dijous_id = self._get_ticket_id(db, "VOLUNTARIAT DE DIJOUS")
            voluntari_divendres_id = self._get_ticket_id(db, "VOLUNTARIAT DE DIVENDRES")
            voluntari_dissabte_id = self._get_ticket_id(db, "VOLUNTARIAT DE DISSABTE")
            acreditacio_organitzacio_id = self._get_ticket_id(db, "ACREDITACIÓ ORGANITZACIÓ")
            acreditacio_cuina_id = self._get_ticket_id(db, "ACREDITACIÓ CUINA")
            acreditacio_comunicacio_id = self._get_ticket_id(db, "ACREDITACIÓ COMUNICACIÓ")
            acreditacio_tresoreria_id = self._get_ticket_id(db, "ACREDITACIÓ TRESORERIA")
            acreditacio_globus_id = self._get_ticket_id(db, "ACREDITACIÓ GLOBUS")
            acreditacio_collaboracio_id = self._get_ticket_id(db, "ACREDITACIÓ COL·LABORACIÓ")
            acreditacio_professional_id = self._get_ticket_id(db, "ACREDITACIÓ PROFESSIONAL")

            entrada_i_voluntariat_del_dia_que_ajuden = {
                self.dijous: [entrada_dijous_id, voluntari_dijous_id],
                self.divendres: [entrada_divendres_id, voluntari_divendres_id],
                self.dissabte: [entrada_dissabte_id, voluntari_dissabte_id],
            }

            self.assignacio_tickets = {
                entrades_id: entrada_i_voluntariat_del_dia_que_ajuden,
                barres_id: entrada_i_voluntariat_del_dia_que_ajuden,
                barres_restringit_id: entrada_i_voluntariat_del_dia_que_ajuden,
                barres_collectiu_torn_id: entrada_i_voluntariat_del_dia_que_ajuden,
                subcaps_barres_id: entrada_i_voluntariat_del_dia_que_ajuden,
                marxandatge_id: entrada_i_voluntariat_del_dia_que_ajuden,
                photocall_id: entrada_i_voluntariat_del_dia_que_ajuden,
                suport_collectius_id: {
                    self.dijous: [entrada_dijous_id],
                    self.divendres: [entrada_divendres_id],
                    self.dissabte: [entrada_dissabte_id],
                },
                muntatge_id: [],
                cuina_id: [acreditacio_cuina_id],
                globus_id: [acreditacio_globus_id],
                tresoreria_id: [acreditacio_tresoreria_id],
                comunicacio_id: [acreditacio_comunicacio_id],
                collaboracio_id: [acreditacio_collaboracio_id],
                organitzacio_id: [acreditacio_organitzacio_id],
                professional_id: [acreditacio_professional_id],
            }

            # ids que necessito
            self.entrada_dijous_id = entrada_dijous_id
            self.entrada_divendres_id = entrada_divendres_id
            self.entrada_dissabte_id = entrada_dissabte_id
            self.abonament_id = abonament_id

            # tasca que com a recompensa tenen una entrada que es dona un dia que no treballen
            self.subcaps_barres_id = subcaps_barres_id

    def calculate_tickets(self, user, current_shifts):
        from .models import UserTicket

        if len(current_shifts) == 0:
            return []

        # amb un diccionari evito àpats duplicats
        tickets_assigned = {}
        def add_ticket(ticket_id):
            if ticket_id not in tickets_assigned:
                ticket = UserTicket(
                    user_id = user.id,
                    ticket_id = ticket_id,
                    ticket_id_options = [ticket_id]
                )
                tickets_assigned[ticket_id] = ticket

        for (t, s, us) in current_shifts:
            the_tickets = self.assignacio_tickets[t.id]
            if type(the_tickets) is dict:
                the_tickets = the_tickets[s.day]

            for ticket_id in the_tickets:
                add_ticket(ticket_id)

        def add_entrades_tres_dies():
            # el poso com a 3 entrades pq posterioment es converteixen en abonament
            add_ticket(self.entrada_dijous_id)
            add_ticket(self.entrada_divendres_id)
            add_ticket(self.entrada_dissabte_id)
            
        def add_entrada_variable():
            free_days = []
            if self.entrada_dijous_id not in tickets_assigned:
                free_days.append(self.entrada_dijous_id)
            if self.entrada_divendres_id not in tickets_assigned:
                free_days.append(self.entrada_divendres_id)
            if self.entrada_dissabte_id not in tickets_assigned:
                free_days.append(self.entrada_dissabte_id)

            if len(free_days) > 0:
                ticket = UserTicket(
                    user_id = user.id,
                    ticket_id = free_days[0],
                    ticket_id_options = free_days
                )
                tickets_assigned[free_days[0]] = ticket

        # reviso si es subcap per donar "entrades variables"
        num_subcaps_tasks = sum(1 for (t, s, us) in current_shifts if t.id == self.subcaps_barres_id)
        if num_subcaps_tasks == 2:
            add_entrada_variable()
        elif num_subcaps_tasks > 3:
            add_entrades_tres_dies()

        # Moment de neteja... si té entrada 3 dies, es canvia per abonament
        if self.entrada_dijous_id in tickets_assigned and self.entrada_divendres_id in tickets_assigned and self.entrada_dissabte_id in tickets_assigned:
            del tickets_assigned[self.entrada_dijous_id]
            del tickets_assigned[self.entrada_divendres_id]
            del tickets_assigned[self.entrada_dissabte_id]

            add_ticket(self.abonament_id)

        # Si hi ha abonament, no calen les entrades de dies sueltos
        if self.abonament_id in tickets_assigned:
            if self.entrada_dijous_id in tickets_assigned: 
                del tickets_assigned[self.entrada_dijous_id]
            if self.entrada_divendres_id in tickets_assigned: 
                del tickets_assigned[self.entrada_divendres_id]
            if self.entrada_dissabte_id in tickets_assigned: 
                del tickets_assigned[self.entrada_dissabte_id]

        # Reviso solapaments d'entrades variables, màxim pot haver 2, i si hi ha 2, deixem sols 1
        there_is_one = False
        for (key, value) in tickets_assigned.items():
            if (key == self.entrada_dijous_id or key == self.entrada_divendres_id or key == self.entrada_dissabte_id) and len(value.ticket_id_options) > 1:
                if there_is_one:
                    del tickets_assigned[key]
                    break
                else:
                    there_is_one = True
                 
        return tickets_assigned.values()

    def calculate_meals(self, user, current_shifts):
        from .models import UserMeal
      
        # amb un diccionari evito àpats duplicats
        meals_assigned = {}

        for (t, s, us) in current_shifts:
            the_meals = self.assignacio_apats[t.id]            
            if type(the_meals) is dict:
                # si és un diccionari, busco el dia
                the_meals = the_meals[s.day]

            # agafo tots els àpats associats a la tasca
            for meal_id in the_meals:
                if meal_id not in meals_assigned:
                    meal = UserMeal(
                        user_id = user.id,
                        meal_id = meal_id,
                        selected = True
                    )
                    meals_assigned[meal_id] = meal 

        return meals_assigned.values()
    
    def calculate_cash(self, current_tickets, current_shifts):
        cash_by_day = {
            self.dijous: 0,
            self.divendres: 0,
            self.dissabte: 0
        }

        cash_lines = []

        # dies en que treballa el voluntari
        busy_days = set()

        cash_to_assign = 0

        def add_cash_detail(task_id, task_day, description, cash):
            nonlocal cash_to_assign

            cash_lines.append(description)
            if task_day not in cash_by_day:
                cash_to_assign += cash
            else:
                cash_by_day[task_day] += cash
            
            if task_day in cash_by_day:
                # controlo que sigui dijous, divendres o dissabte
                busy_days.add(task_day)

        for (t, s, us) in current_shifts:
            if s.reward > 0:
                if s.assignations: # no es buit, és a dir, hi ha opcions
                    zero_assignations = True
                    for (name, assigned) in zip(s.assignations, us.shift_assignations):
                        if assigned:
                            add_cash_detail(t.id, s.day, f"{t.name} - {s.description} - {name}: {s.reward} €", s.reward)
                            zero_assignations = False
                        
                    if zero_assignations:
                        if s.direct_reward:
                            # tant se val, recompensa directa
                            add_cash_detail(t.id, s.day, f"{t.name} - {s.description}: {s.reward} €", s.reward)
                        else:
                            add_cash_detail(t.id, s.day, f"{t.name} - {s.description}: {s.reward} € [{labels.get('reward_assignation_pending')}]", 0)
                else:
                    # no hi ha opcions, es recomensa directa
                    add_cash_detail(t.id, s.day, f"{t.name} - {s.description}: {s.reward} €", s.reward)

        if cash_to_assign > 0:
            free_days = []
            # es tracta de repartir aquests diners entre els dies que no treballa, o si no entre els que treball equitativament

            if self.dijous not in busy_days and (self.entrada_dijous_id in current_tickets or self.abonament_id in current_tickets):
                free_days.append(self.dijous)

            if self.divendres not in busy_days and (self.entrada_divendres_id in current_tickets or self.abonament_id in current_tickets):
                free_days.append(self.divendres)

            if self.dissabte not in busy_days and (self.entrada_dissabte_id in current_tickets or self.abonament_id in current_tickets):
                free_days.append(self.dissabte)

            if not free_days:
                # no te dies lliures, es reparteix entre els dies ocupats
                if busy_days:
                    free_days = list(busy_days)
                else:
                    # segurament és una acreditació, es dona el 1r dia i ja està
                    free_days = [self.dijous]
            
            integer_cash_by_day = cash_to_assign // len(free_days)
            for d in free_days:
                cash_by_day[d] = cash_by_day[d] + integer_cash_by_day

            remanent = cash_to_assign - len(free_days)*integer_cash_by_day
            cash_by_day[free_days[0]] = cash_by_day[free_days[0]] + remanent

        return (cash_by_day, cash_lines)
    

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
            self.update_rewards(user, with_notification = False)

    def update_rewards(self, user, with_notification = True):
        # miro quins torns fa l'usuari
        current_shifts = self.__get_current_shifts(user.id)

        logger.info(f"Update rewards of {user.full_name}")

        # actualitzo tickets, acreditacions i àpats
        self.__update_tickets(user, current_shifts)
        self.__update_meals(user, current_shifts)

        # actualitzo el cash
        self.update_cash(user.id)

        # actualitzo el last_change_at de l'usuari
        if with_notification:
            self.__update_user(user)

    def __get_current_shifts(self, user_id):
        from .models import UserShift, Shift, Task
        from . import db

        return db.session.query(Task, Shift, UserShift).join(Shift, Task.id == Shift.task_id).join(UserShift).filter(UserShift.user_id == user_id).order_by(Shift.id.asc()).all()

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
            existing_ticket = self.__get_first_with_filter(lambda t:t.ticket_id_options == ticket.ticket_id_options, current_tickets)
            if existing_ticket:
                ticket.ticket_id = existing_ticket.ticket_id

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

    def update_cash(self, user_id):
        from .models import UserTicket, UserRewards
        from . import db

        rewards = UserRewards.query.filter_by(user_id = user_id).first()
        if not rewards:
            # usuari no validat, no cal fer res
            return

        current_tickets = [id[0] for id in db.session.query(UserTicket.ticket_id).filter(UserTicket.user_id == user_id).all()]

        (cash_by_day, cash_lines) = self.rewards_instance.calculate_cash(
            current_tickets = current_tickets,
            current_shifts = self.__get_current_shifts(user_id)
        )
       
        rewards.description = cash_lines
        cash_total = 0
        for (k,v) in cash_by_day.items():
            rewards.cash_by_day[k] = str(v)
            cash_total += v
        db.session.add(rewards)

        logger.info(f"USER #{user_id} ==> {cash_total} €")
