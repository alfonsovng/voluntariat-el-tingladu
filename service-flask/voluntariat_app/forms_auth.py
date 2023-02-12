from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from .helper import trim

class SignUpForm(FlaskForm):
    name = StringField("Nom", validators=[DataRequired()], filters = [trim])
    surname = StringField("Cognoms", validators=[DataRequired()], filters = [trim])
    email = StringField(
        "Email",
        validators=[
            Length(min=6),
            Email(message="Introdueix una adreça de correu vàlida"),
            DataRequired(),
        ],
        filters = [trim]
    )
    phone = StringField("Mòbil", filters = [trim])
    adult = BooleanField(
        "Sóc major d'edat",
        validators=[DataRequired()]
    )
    store_email = BooleanField(
        "Accepto rebre emails d'El Tingladu i que el meu email sigui emmagatzemat per a futurs esdeveniments",
        validators=[DataRequired()]
    )
    submit = SubmitField("Registra't")

class ForgottenPasswordForm(FlaskForm):
    email = StringField(
        "Email", validators=[DataRequired(), 
        Email(message="Introdueix una adreça de correu vàlida")],
        filters = [trim]
    )
    submit = SubmitField("Restaura la contrasenya")

class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "Contrasenya",
        validators=[
            DataRequired(),
            Length(min=6, message="La contrasenya ha de tenir més de 6 caràcters"),
        ],
    )
    confirm = PasswordField(
        "Confirma la contrasenya",
        validators=[
            DataRequired(),
            EqualTo("password", message="Les contrasenyes han de ser iguals"),
        ],
    )
    submit = SubmitField("Canvia la contrasenya")

class LoginForm(FlaskForm):
    email = StringField(
        "Email", 
        validators=[DataRequired(), Email(message="Introdueix una adreça de correu vàlida")],
        filters = [trim]
    )
    password = PasswordField("Contrasenya", validators=[DataRequired()])
    submit = SubmitField("Entra")
