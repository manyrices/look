from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from ..models import User

class LoginForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Keep logged in')
	submit = SubmitField('Submit')

class RegistrationForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
	username = StringField('Username', validators=[DataRequired(), Length(1,64), Regexp(
		'^[A-Za-z][A-Za-z0-9_.]*$',0,'Username must have only letters,numbers,dots or underscores')])
	password = PasswordField('Password', validators=[DataRequired(),EqualTo(
		'password2', message='Password must match')])
	password2 = PasswordField('Confirm password', validators=[DataRequired()])
	submit = SubmitField('Submit')

	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('Email already registered.')
	def validate_username(self, field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError('Username already in use.')

class ChangePasswordForm(FlaskForm):
	old_password = PasswordField('Old password', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired(),EqualTo(
		'password2', message='Password must match')])
	password2 = PasswordField('Confirm password', validators=[DataRequired()])
	submit = SubmitField('Submit')

class ChangeEmailForm(FlaskForm):
	password = PasswordField('Confirm password', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
	submit = SubmitField('Update email')

	def validate_email(self, field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('Email already registered.')

class PasswordResetRequestForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
	submit = SubmitField('Reset password')


class PasswordResetForm(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired(),EqualTo(
		'password2', message='Password must match')])
	password2 = PasswordField('Confirm password', validators=[DataRequired()])
	submit = SubmitField('Submit')
