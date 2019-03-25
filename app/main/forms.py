from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, BooleanField, SelectField, StringField, ValidationError
from wtforms.validators import DataRequired, Length, Regexp, Email
from ..models import User, Role, Post, Permission
from flask_pagedown.fields import PageDownField

class PostForm(FlaskForm):
	body = PageDownField('What is your mind?', validators=[DataRequired()])
	submit = SubmitField('Submit')

class EditProfileAdminForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Length(1, 64),
											Email()])
	username = StringField('Username', validators=[DataRequired(), Length(1, 64),
												Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
													   'Usernames must hava only letters, \
													   numbers,dots or \
													   underscores')])
	confirmed = BooleanField('Confirmed')
	role = SelectField('Role', coerce=int)
	about_me = TextAreaField('About_me')
	submit = SubmitField('Submit')

	def __init__(self, user, *args, **kwargs):
		super(EditProfileAdminForm, self).__init__(*args, **kwargs)
		self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
		self.user = user

	def validate_email(self, field):
		if field.data != self.user.email and \
					User.query.filter_by(email=field.data).first():
			raise ValidationError('Email already registered.')

	def validate_username(self, field):
		if field.data != self.username and \
					User.query.filter_by(username=field.data).first():
			raise ValidationError('Username already in use.')

class CommentForm(FlaskForm):
	body = StringField('', validators=[DataRequired()])
	submit = SubmitField('Submit')