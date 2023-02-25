from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from .helper import trim

class NewWorkerForm(FlaskForm):
    surname = StringField("Cognoms", filters = [trim], validators=[DataRequired()])
    name = StringField("Nom", filters = [trim])
    phone = StringField("Mòbil", filters = [trim])
    shifts = SelectField(
        "Torn preassignat", 
        choices=[]
    )
    submit = SubmitField("Dona d'alta")

class NewWorkerBatchForm(FlaskForm):
    prefix = StringField("Prefix", filters = [trim], validators=[DataRequired()])
    shifts = SelectField(
        "Torn preassignat", 
        choices=[]
    )
    submit = SubmitField("Dona d'alta")

class WorkerForm(FlaskForm):
    surname = StringField("Cognoms", filters = [trim], validators=[DataRequired()])
    name = StringField("Nom", filters = [trim])
    phone = StringField("Mòbil", filters = [trim])
    submit = SubmitField("Actualitza")

class AssignationsForm(FlaskForm):
    submit = SubmitField("Guarda les assignacions")