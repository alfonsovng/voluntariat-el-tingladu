from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, EqualTo
from .helper import trim

class ProfileForm(FlaskForm):
    name = StringField("Nom", filters = [trim], validators=[DataRequired()])
    surname = StringField("Cognoms", filters = [trim], validators=[DataRequired()])
    phone = StringField("Mòbil", filters = [trim])
    ticket1 = StringField("Si ja tens l'entrada comprada, indica'ns el localitzador", filters = [trim])
    ticket2 = StringField("Si ja tens l'entrada comprada, indica'ns el localitzador", filters = [trim])
    ticket3 = StringField("Si ja tens l'entrada comprada, indica'ns el localitzador", filters = [trim])
    ticket4 = StringField("Si ja tens l'entrada comprada, indica'ns el localitzador", filters = [trim])
    submit = SubmitField("Actualiza les dades")

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(
        "Contrasenya actual",
        validators=[
            DataRequired()
        ],
    )
    new_password = PasswordField(
        "Nova contrasenya",
        validators=[
            DataRequired(),
            Length(min=6, message="La nova contrasenya ha de tenir més de 6 caràcters"),
        ],
    )
    confirm = PasswordField(
        "Confirma la nova contrasenya",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Les contrasenyes han de ser iguals"),
        ],
    )
    submit = SubmitField("Canvia la contrasenya")

class ShiftsForm(FlaskForm):
    submit = SubmitField("Actualitza els teus torns")

class ShiftsFormWithPassword(FlaskForm):
    submit = SubmitField("Actualitza els teus torns")
    password = StringField(
        "Contrasenya per apuntar-se a aquests torns",
        validators=[DataRequired()]
    )
