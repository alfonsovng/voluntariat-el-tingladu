from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo
from .helper import trim

class ProfileForm(FlaskForm):
    name = StringField(filters = [trim], validators=[DataRequired()])
    surname = StringField(filters = [trim], validators=[DataRequired()])
    phone = StringField(filters = [trim])
    purchased_ticket1 = StringField(filters = [trim])
    purchased_ticket2 = StringField(filters = [trim])
    purchased_ticket3 = StringField(filters = [trim])
    purchased_ticket4 = StringField(filters = [trim])
    electrician = BooleanField()
    submit = SubmitField()

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(
        validators=[
            DataRequired()
        ],
    )
    new_password = PasswordField(
        validators=[
            DataRequired(),
            Length(min=6),
        ],
    )
    confirm = PasswordField(
        validators=[
            DataRequired(),
            EqualTo("new_password"),
        ],
    )
    submit = SubmitField()

class ShiftsForm(FlaskForm):
    submit = SubmitField()

class ShiftsFormWithPassword(FlaskForm):
    submit = SubmitField()
    password = StringField(validators=[DataRequired()])

class DietForm(FlaskForm):
    vegan = BooleanField()
    vegetarian = BooleanField()
    no_gluten = BooleanField()
    no_lactose = BooleanField()
    comments = TextAreaField(filters = [trim])
    accept_conditions_diet = BooleanField(validators=[DataRequired()])
    submit = SubmitField()

class MealsForm(FlaskForm):
    # accept_conditions_meals = BooleanField(validators=[DataRequired()])
    submit = SubmitField()

class TicketsForm(FlaskForm):
    submit = SubmitField()