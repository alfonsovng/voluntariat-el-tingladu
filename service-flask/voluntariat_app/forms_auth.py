from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from .helper import trim

class SignUpForm(FlaskForm):
    name = StringField(validators=[DataRequired()], filters = [trim])
    surname = StringField(validators=[DataRequired()], filters = [trim])
    email = StringField(
        validators=[
            Length(min=6),
            Email(),
            DataRequired(),
        ],
        filters = [trim]
    )
    dni = StringField(validators=[DataRequired()], filters = [trim])
    phone = StringField(filters = [trim])
    adult = BooleanField(
        validators=[DataRequired()]
    )
    store_email = BooleanField(
        validators=[DataRequired()]
    )
    contract = BooleanField(
        validators=[DataRequired()]
    )
    submit = SubmitField()

class ForgottenPasswordForm(FlaskForm):
    email = StringField(validators=[DataRequired()], 
        filters = [trim]
    )
    submit = SubmitField()

class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        validators=[
            DataRequired(),
            Length(min=6),
        ],
    )
    confirm = PasswordField(
        validators=[
            DataRequired(),
            EqualTo("password"),
        ],
    )
    submit = SubmitField()

class LoginForm(FlaskForm):
    email = StringField(
        validators=[DataRequired()],
        filters = [trim]
    )
    password = PasswordField(validators=[DataRequired()])
    submit = SubmitField()
