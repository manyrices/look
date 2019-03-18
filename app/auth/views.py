from . import auth
from .. import db
from ..helper import random_string
from ..models import User
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, ChangeEmailForm, \
	PasswordResetRequestForm, PasswordResetForm
from flask import render_template, request, url_for, redirect, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from ..email import send_email 


@auth.before_app_request
def before_request():
	if current_user.is_authenticated:
		current_user.ping()
		if not current_user.confirmed \
			and request.endpoint \
			and request.blueprint != 'auth' \
			and request.endpoint != 'static':
			return redirect(url_for('auth.unconfirmed'))

#未邮件确认页面
@auth.route('/unconfirmed')
def unconfirmed():
	if current_user.is_anonymous or current_user.confirmed:
		return redirect(url_for('main.index'))
	return render_template('auth/unconfirmed.html')

#登录
@auth.route('/login', methods=['GET','POST'])
def login():
	form = LoginForm()
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			next = request.args.get('next')
			if next is None or next.startswith('/'):
				next = url_for('main.index')
			return redirect(next)
		flash('Invalid username or password.')
	return render_template('auth/login.html', form=form)

#注销
@auth.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out.')
	return redirect(url_for('main.index'))

#注册&发送确认邮件
@auth.route('/register', methods=['GET','POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(email=form.email.data, username=form.username.data, 
			password=form.password.data)
		db.session.add(user)
		db.session.commit()
		login_user(user, remember=True)
		token = user.generate_confirmation_token()
		send_email(user.email, 'Confirm your account', '/auth/email/confirm',user=user,token=token)
		flash('A confirmation email has been sent to you by email.')
		return redirect(url_for('auth.unconfirmed'))
	return render_template('auth/register.html', form=form)

#生成确认邮件
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
	if current_user.confirmed:
		return redirect(url_for('main.index'))
	if current_user.confirm(token):
		db.session.commit()
		flash('You have confirmed your account, Thanks.')
	else:
		flash('The confirmation link is Invalid.')
	return redirect(url_for('main.index'))

#重新发送确认邮件
@auth.route('/confirm')
@login_required
def resend_confirmation():
	token = current_user.generate_confirmation_token()
	send_email(current_user.email, 'Confirm your account', '/auth/email/confirm',user=current_user,token=token)
	flash('A confirmation email has been sent to you by email.')
	return redirect(url_for('main.index'))

#发送重置密码邮件
@auth.route('/reset', methods=['GET','POST'])
def password_reset_request():
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	form = PasswordResetRequestForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user:
			token = User.generate_reset_token
			send_email(user.email, 'Reset your password', 
				'/auth/email/reset_password',
				user=user, token=token,
				next=request.args.get('next'))
		flash('An email with instructions to reset your password has been sent to you.')
		return redirect(url_for('auth.login'))
	return render_template('auth/reset_password.html', form=form)

#生成重置密码链接
@auth.route('/reset/<token>', methods=['GET','POST'])
def password_reset(token):
	if not current_user.is_anonymous:
		return redirect(url_for('main.index'))
	form = PasswordResetForm()
	if form.validate_on_submit():
		if User.reset_password(token, form.password.data):
			db.session.commit()
			flash('Your password has been update.')
			return redirect(url_for('auth.login'))
		else:
			return redirect(url_for('main.index'))
	return render_template('auth/reset_password.html', form=form)


#修改密码
@auth.route('/change_password', methods=['GET','POST'])
@login_required
def change_password():
	form = ChangePasswordForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.oldpassword.data):
			current_user.password = form.password.data
			db.session.add(current_user)
			db.session.commit()
			flash('Your password has been update.')
		else:
			flash('Invalid password.')
	return render_template('auth/change_password.html', form=form)


#发送修改邮箱链接
@auth.route('/change_email', methods=['GET','POST'])
@login_required
def change_email_request():
	form = ChangeEmailForm()
	if form.validate_on_submit():
		if current_user.verify_password(form.password.data):
			new_email = form.email.data
			token = current_user.generate_change_email_token(new_email)
			send_email(new_email, 'Confirmed your email address.', 
				'/auth/email/change_email', user=current_user, token=token)
			flash('An email with instructions to confirm your new email \
				address has been sent to you.')
			return redirect(url_for('main.index'))
		else:
			flash('Invalid email or password.')
	return render_template('auth/change_email.html', form=form)

#修改邮箱
@auth.route('/change_email/<token>')
@login_required
def change_email(token):
	if current_user.change_email(token):
		db.session.commit()
		flash('Your email address has been updated.')
	else:
		flash('Invalid request.')
	return redirect(url_for('main.index'))