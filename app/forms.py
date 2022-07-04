from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo

from app.models import User

formats = ["Standard", "Historic", "Pioneer", "Modern", "Legacy", "Commander"]


class ViewForm(FlaskForm):
	submit = SubmitField('Submit a Sideboard Guide')


class VoteForm(FlaskForm):
	up = SubmitField('Upvote')
	down = SubmitField('Downvote')


class LoginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Sign In')


class DeckBuilderForm(FlaskForm):
	formatfield = SelectField(label='Format', choices=[(x.lower(), x) for x in formats])
	namefield = TextAreaField('Deck Name', validators=[DataRequired()])
	deckfield = TextAreaField('Decklist', validators=[DataRequired()])
	sidefield = TextAreaField('Sideboard', validators=[DataRequired()])
	hidden = BooleanField('Hidden')
	submit = SubmitField('Submit')


class SideForm(FlaskForm):
	side_out = TextAreaField('Out', validators=[DataRequired()])
	side_in = TextAreaField('In', validators=[DataRequired()])
	explanation = TextAreaField('Explanation', validators=[DataRequired()])
	submit = SubmitField('Submit')


class RegistrationForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	password2 = PasswordField(
		'Confirm Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Register')

	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user is not None:
			raise ValidationError('Please use a different username.')

	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user is not None:
			raise ValidationError('Please use a different email address.')

