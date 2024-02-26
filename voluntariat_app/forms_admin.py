from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from .helper import trim

class AddWorkerForm(FlaskForm):
    surname = StringField(filters = [trim], validators=[DataRequired()])
    name = StringField(filters = [trim])
    phone = StringField(filters = [trim])
    shifts = SelectField(choices=[])
    submit = SubmitField()

class AddSomeWorkersForm(FlaskForm):
    prefix = StringField(filters = [trim], validators=[DataRequired()])
    number = IntegerField(validators=[NumberRange(min=1,max=50)])
    shifts = SelectField(choices=[])
    submit = SubmitField()

class WorkerForm(FlaskForm):
    surname = StringField(filters = [trim], validators=[DataRequired()])
    name = StringField(filters = [trim])
    phone = StringField(filters = [trim])
    submit = SubmitField()

class AssignationsForm(FlaskForm):
    submit = SubmitField()

class TaskPasswordForm(FlaskForm):
    submit = SubmitField()

class ShiftSlotsForm(FlaskForm):
    submit = SubmitField()