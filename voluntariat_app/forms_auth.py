from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp
from .helper import trim
import re

class SignUpForm(FlaskForm):
    email = StringField(
        validators=[
            Length(min=6),
            Email(),
            DataRequired(),
        ],
        filters = [trim]
    )
    dni = StringField(validators=[DataRequired()], filters = [trim])
    adult = BooleanField(
        validators=[DataRequired()]
    )
    store_email = BooleanField(
        validators=[DataRequired()]
    )
    contract = BooleanField(
        validators=[DataRequired()]
    )
    data_protection = BooleanField(
        validators=[DataRequired()]
    )
    submit = SubmitField()

class RegisterForm(FlaskForm):
    name = StringField(validators=[DataRequired()], filters = [trim])
    surname = StringField(validators=[DataRequired()], filters = [trim])
    phone = StringField(filters = [trim])
    electrician = BooleanField()

    contract = BooleanField(
        validators=[DataRequired()]
    )
    data_protection = BooleanField(
        validators=[DataRequired()]
    )

    email_confirmation = StringField(filters = [trim])

    def set_email_confirmation(self, email):
        self.email_confirmation.validators = [Regexp(email, flags=re.IGNORECASE)]
    
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
    adult = BooleanField(
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
