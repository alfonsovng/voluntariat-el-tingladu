from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from .helper import trim

class AddWorkerForm(FlaskForm):
    surname = StringField("Cognoms", filters = [trim], validators=[DataRequired()])
    name = StringField("Nom", filters = [trim])
    phone = StringField("Mòbil", filters = [trim])
    shifts = SelectField(
        "Torn preassignat", 
        choices=[]
    )
    submit = SubmitField("Dona d'alta")

class AddSomeWorkersForm(FlaskForm):
    prefix = StringField("Prefix", filters = [trim], validators=[DataRequired()])
    number = IntegerField("Nombre de persones treballadors", validators=[NumberRange(min=1,max=50)])
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