from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, TextAreaField, StringField
from wtforms.validators import DataRequired
from .helper import trim

class IncidenceForm(FlaskForm):
    type = SelectField(
        "Tipus d'incidència", 
        choices=[
            "Error en la web",
            "Canvi d'adreça d'email",
            "No puc fer una tasca o torn",
            "Desacord amb la recompensa",
            "Problema amb la dieta",
            "Altre tipus d'incidència"
        ]
    )
    description = TextAreaField(
        "Descripció de l'incidència", 
        validators=[
            DataRequired()
        ],
        filters = [trim]
    )
    submit = SubmitField("Envia l'incidència")

class EmailForm(FlaskForm):
    subject = StringField("Assumpte", validators=[DataRequired()])
    body = TextAreaField(
        "Contingut del missatge", 
        validators=[
            DataRequired()
        ],
        filters = [trim]
    )
    submit = SubmitField("Envia el missatge")