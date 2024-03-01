from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from .helper import trim

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
    purchased_ticket1 = StringField(filters = [trim])
    purchased_ticket2 = StringField(filters = [trim])
    purchased_ticket3 = StringField(filters = [trim])
    electrician = BooleanField()
    comments = TextAreaField(filters = [trim])

    contract = BooleanField(
        validators=[DataRequired()]
    )
    data_protection = BooleanField(
        validators=[DataRequired()]
    )

    email_confirmation = StringField(validators=[DataRequired()], filters = [trim])
    
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
