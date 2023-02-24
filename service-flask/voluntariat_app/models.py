from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import enum
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import text, exists
from . import db, hashid_manager

class UserRole(enum.Enum):
    admin = 1
    volunteer = 2
    worker = 3

class UserShift(db.Model):
    __tablename__ = "user_shifts"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey("shifts.id"), primary_key=True)
    shift_assignations = db.Column(ARRAY(db.Boolean), nullable=False, default=[])
    comments = db.Column(db.String, nullable=False, server_default='') #'' es un possible valor

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    dni = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False, server_default='')    #'' es un possible valor
    purchased_ticket1 = db.Column(db.String, nullable=False, server_default='')  #'' es un possible valor
    purchased_ticket2 = db.Column(db.String, nullable=False, server_default='')  #'' es un possible valor
    purchased_ticket3 = db.Column(db.String, nullable=False, server_default='')  #'' es un possible valor
    purchased_ticket4 = db.Column(db.String, nullable=False, server_default='')  #'' es un possible valor
    electrician = db.Column(db.Boolean, nullable=False, default=False, server_default=text("FALSE"))
    role = db.Column(db.Enum(UserRole, name='users_role'), nullable=False)
    change_password_token = db.Column(db.String)
    # aliased pq quan fem join de user amb user_shifts no doni problemes
    has_shifts = db.column_property(exists().where(aliased(UserShift,name="user_shifts_to_count_them").user_id==id))

    @hybrid_property
    def hashid(self):
        return hashid_manager.get_hashid(self.id)

    @hybrid_property
    def full_name(self):
        return f"{self.surname}, {self.name}"

    @hybrid_property
    def is_admin(self):
        return self.role == UserRole.admin

    @hybrid_property
    def is_worker(self):
        return self.role == UserRole.worker

    def set_password(self, password):
        """Assigna un password amb la funció hash aplicada"""
        self.password = generate_password_hash(password, method="sha256")

    def check_password(self, password):
        """Comprova si el password és igual"""
        return check_password_hash(self.password, password)

    def __repr__(self):
        return "<User {}>".format(self.id)

class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String, nullable=False, server_default='') #'' es un possible valor
    password = db.Column(db.String, nullable=False, server_default='') #'' es un possible valor

class Shift(db.Model):
    __tablename__ = "shifts"
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False, server_default='') #'' es un possible valor
    slots = db.Column(db.Integer, nullable=False, server_default=text("0")) # 0 significa sense límits
    assignations = db.Column(ARRAY(db.String), nullable=False, server_default='{}') # opcions que assigna l'admin
    reward = db.Column(db.Integer, nullable=False, server_default=text("0")) # recompensa en tiquets

class UserDiet(db.Model):
    __tablename__ = "user_diets"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    vegan = db.Column(db.Boolean, nullable=False, default=False, server_default=text("FALSE"))
    vegetarian = db.Column(db.Boolean, nullable=False, default=False, server_default=text("FALSE"))
    no_gluten = db.Column(db.Boolean, nullable=False, default=False, server_default=text("FALSE"))
    no_lactose = db.Column(db.Boolean, nullable=False, default=False, server_default=text("FALSE"))
    comments = db.Column(db.String, nullable=False, default='', server_default='') #'' es un possible valor

class Meal(db.Model):
    __tablename__ = "meals"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String, nullable=False, server_default='') #'' es un possible valor

class UserMeal(db.Model):
    __tablename__ = "user_meals"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey("meals.id"), primary_key=True)
    selected = db.Column(db.Boolean, nullable=False, default=False, server_default=text("FALSE"))
    comments = db.Column(db.String, nullable=False, server_default='') #'' es un possible valor

class Ticket(db.Model):
    __tablename__ = "tickets"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description = db.Column(db.String, nullable=False) #'' es un possible valor

class UserTicket(db.Model):
    __tablename__ = "user_tickets"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), primary_key=True)
    selected = db.Column(db.Boolean, nullable=False, default=False, server_default=text("FALSE"))
