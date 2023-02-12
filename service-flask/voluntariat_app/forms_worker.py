from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from .helper import trim

class NewWorkerForm(FlaskForm):
    name = StringField("Nom", filters = [trim], validators=[DataRequired()])
    place = StringField("Lloc", filters = [trim], validators=[DataRequired()])
    submit = SubmitField("Dona d'alta")

class WorkerForm(FlaskForm):
    name = StringField("Nom", filters = [trim], validators=[DataRequired()])
    place = StringField("Lloc", filters = [trim], validators=[DataRequired()])
    submit = SubmitField("Actualitza")