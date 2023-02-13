from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo
from .helper import trim

# class MultiCheckboxField(SelectMultipleField):
#     widget = widgets.ListWidget(prefix_label=False)
#     option_widget = widgets.CheckboxInput()

class ProfileForm(FlaskForm):
    name = StringField("Nom", filters = [trim], validators=[DataRequired()])
    surname = StringField("Cognoms", filters = [trim], validators=[DataRequired()])
    phone = StringField("Mòbil", filters = [trim])
    purchased_ticket1 = StringField("Si ja tens l'entrada comprada, indica'ns el localitzador", filters = [trim])
    purchased_ticket2 = StringField("Si ja tens l'entrada comprada, indica'ns el localitzador", filters = [trim])
    purchased_ticket3 = StringField("Si ja tens l'entrada comprada, indica'ns el localitzador", filters = [trim])
    purchased_ticket4 = StringField("Si ja tens l'entrada comprada, indica'ns el localitzador", filters = [trim])
    electrician = BooleanField("Domines d'electricitat?")
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

class DietForm(FlaskForm):
    vegan = BooleanField("Dieta vegana")
    vegetarian = BooleanField("Dieta vegetariana")
    no_gluten = BooleanField("Dieta sense gluten")
    no_lactose = BooleanField("Dieta sense lactosa")
    comments = TextAreaField(
        "Altres intoleràncies o al·lèrgies, o observacions que vulguis afegir", 
        filters = [trim]
    )
    accept_conditions = BooleanField(
        "Entenc que la cuina d'El Tingladu tindrà en compte les vostres especificitats alimentàries, però no podem garantir una adaptació completa a cada dieta",
        validators=[DataRequired()]
    )
    submit = SubmitField("Actualitza la teva dieta")

class MealsForm(FlaskForm):
    submit = SubmitField("Actualitza els teus àpats")

class TicketsForm(FlaskForm):
    submit = SubmitField("Actualitza les teves entrades")