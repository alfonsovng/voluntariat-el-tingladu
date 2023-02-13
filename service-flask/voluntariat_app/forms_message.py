from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, TextAreaField, StringField
from wtforms.validators import DataRequired
from .helper import trim

class IncidenceForm(FlaskForm):
    type = SelectField(
        "Tipus d'incidència", 
        choices=[
            "Arribaré tard al torn",
            "No puc fer un torn",
            "Problema amb la dieta o els àpats",
            "Canvi d'adreça d'email o DNI",
            "Error en en l'aplicatiu",
            "Suggeriment o millora en l'aplicatiu",
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
    subject = StringField("Assumpte", validators=[DataRequired()], filters = [trim])
    body = TextAreaField(
        "Contingut del missatge", 
        validators=[
            DataRequired()
        ],
        filters = [trim]
    )
    submit = SubmitField("Envia el missatge")