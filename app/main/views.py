import os
from .forms import PostForm, EditProfileAdminForm
from . import main
from .. import db
from ..models import User, Role, Post, Permission
from flask import render_template ,redirect, url_for, request, current_app, jsonify, flash, abort
from ..helper import random_string
from ..decorators import admin_required
from flask_login import current_user, login_required

#看看文章首页
@main.route('/', methods=['GET','POST'])
def index():
	form = PostForm()
	if current_user.can(Permission.WRITE) and form.validate_on_submit():
		post = Post(body=form.body.data, 
					author=current_user._get_current_object())
		db.session.add(post)
		db.session.commit()
		return redirect(url_for('.index'))
	#flask分页类的实现
	page = request.args.get('page', 1, type=int)
	pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
		page, per_page=current_app.config['LOOK_POSTS_PER_PAGE'],
		error_out=False)
	posts = pagination.items
	return render_template('index.html', form=form, posts=posts, pagination=pagination)

#文章固定链接
@main.route('/post/<int:id>')
def post(id):
	post = Post.query.get_or_404(id)
	return render_template('post.html', posts=[post])

#文章编辑
@main.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and \
			not current_user.can(Permission.ADMIN):
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.body = form.body.data
		db.session.add(post)
		db.session.commit()
		flash('Post has been updated.')
	form.body.data = post.body
	return render_template('edit_post.html', form=form)


#用户资料页面
@main.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	posts = user.posts.order_by(Post.timestamp.desc()).all()
	return render_template('user.html', user=user, posts=posts)

#用户个性描述编辑
@main.route('/upload_aboutme')
@login_required
def upload_aboutme():
	user = current_user._get_current_object()
	if user:
		about_me = request.args.get('foo')
		if not about_me:
			about_me = 'The user is lazy, there is nothing left.'
		user.about_me = about_me
		db.session.add(user)
		db.session.commit()
		return jsonify(data=1)
	return jsonify(data=0)

#头像编辑页面
@main.route('/edit_avatar', methods=['GET','POST'])
@login_required
def edit_avatar():
	user = current_user._get_current_object()
	return render_template('/edit_avatar.html', user=user)

#用户头像上传与编辑
@main.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
	file = request.files['avatar'].read()
	user = current_user._get_current_object() #获取当前真实登录用户
	if user is None:
		redirect(url_for('main.index'))
	# cropper插件传输文件格式为二进制流，因此file文件类操作不能实现
	# if file.filename == '':
	# 	return redirect(url_for('main.edit_avatar'))
	# if file and allowed_file(file.filename):
	# 	filename = secure_filename(file.filename)
	# 	filename = random_string(32) + get_file_suffix_name(filename)
	# 	avatar = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
	# 	with open(avatar, 'wb+') as f:
	# 		f.write(data)
	# 	return jsonify(data=1)
	# return jsonify(data=0)
	if file:
		filename = random_string(32) + '.jpg'
		avatar = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
		if user.avatar != 'default_avatar.jpg':
			os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], user.avatar))
		with open(avatar, 'wb+') as f:
			f.write(file)
		user.avatar = filename
		db.session.add(user)
		db.session.commit()
		return jsonify(data=1)
	return jsonify(data=0)

#管理员编辑用户资料
@main.route('/edit-profile/<int:id>', methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form = EditProfileAdminForm(user=user)
	if form.validate_on_submit():
		user.email = form.email.data
		user.username = form.username.data
		user.confirmed = form.confirmed.data
		user.role = Role.query.get(form.role.data)
		if not form.about_me.data:
			form.about_me.data = 'The user is lazy, there is nothing left.'
		user.about_me = form.about_me.data
		db.session.add(user)
		db.session.commit()
		flash('The profile has been updated.')
		return redirect(url_for('.user', username=user.username ))
	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.about_me.data = user.about_me
	return render_template('edit_profile.html', form=form, user=user)