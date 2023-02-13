from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from .helper import trim

class NewWorkerForm(FlaskForm):
    surname = StringField("Cognoms", filters = [trim], validators=[DataRequired()])
    name = StringField("Nom", filters = [trim], validators=[DataRequired()])
    phone = StringField("Mòbil", filters = [trim])
    submit = SubmitField("Dona d'alta")

class WorkerForm(FlaskForm):
    surname = StringField("Cognoms", filters = [trim], validators=[DataRequired()])
    name = StringField("Nom", filters = [trim], validators=[DataRequired()])
    phone = StringField("Mòbil", filters = [trim])
    submit = SubmitField("Actualitza")