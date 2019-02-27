from . import auth
from .. import db
from ..models import User
from .forms import LoginForm, RegistrationForm
from flask import render_template, request, url_for, redirect, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..email import send_email 

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

#邮件确认
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