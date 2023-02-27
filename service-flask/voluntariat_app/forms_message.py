from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField, TextAreaField, StringField
from wtforms.validators import DataRequired
from .helper import trim

class IncidenceForm(FlaskForm):
    type = SelectField(choices=[])
    description = TextAreaField(
        validators=[
            DataRequired()
        ],
        filters = [trim]
    )
    submit = SubmitField()

class EmailForm(FlaskForm):
    subject = StringField(validators=[DataRequired()], filters = [trim])
    body = TextAreaField(
        validators=[
            DataRequired()
        ],
        filters = [trim]
    )
    submit = SubmitField()