import os
from .forms import PostForm, EditProfileAdminForm, CommentForm
from sqlalchemy.exc import IntegrityError
from . import main
from .. import db
from ..models import User, Role, Post, Permission, Comment
from flask import render_template ,redirect, url_for, request, current_app, jsonify, flash, abort, make_response
from ..helper import random_string
from ..decorators import admin_required, permission_required
from flask_login import current_user, login_required

#首页(页面)
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
	show_followed = False
	if current_user.is_authenticated:
		show_followed = bool(request.cookies.get('show_followed', ''))
	if show_followed:
		query = current_user.followed_posts
	else:
		query = Post.query
	pagination = query.order_by(Post.timestamp.desc()).paginate(
					page, per_page=current_app.config['LOOK_POSTS_PER_PAGE'],
					error_out=False)
	posts = pagination.items
	return render_template('index.html', form=form, posts=posts, 
					show_followed=show_followed, pagination=pagination)

#文章(页面)
@main.route('/post/<int:id>', methods=['GET','POST'])
def post(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body=form.body.data,
						  post=post,
						  author=current_user._get_current_object())
		db.session.add(comment)
		db.session.commit()
		return redirect(url_for('.post', id=post.id, page=-1)) #-1用于请求评论最后一页
	page = request.args.get('page', 1, type=int)
	if page == -1:
		page = (post.comments.count() - 1) // \
				current_app.config['LOOK_POSTS_PER_PAGE'] + 1
	pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
		page, per_page=current_app.config['LOOK_POSTS_PER_PAGE'],
		error_out=False)
	comments = pagination.items
	return render_template('post.html', posts=[post], form=form,
							comments=comments, pagination=pagination)

#文章编辑(页面)
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
	return render_template('edit_post.html', form=form, post=post)

#文章删除(功能)
@main.route('/remove/<int:id>')
@login_required
@admin_required
def remove(id):
	post = Post.query.filter_by(id=id).first()
	if post is None:
		flash('Post does not exist.')
		return redirect(url_for('.index'))
	if not current_user.can(Permission.ADMIN):
		flash('You has not permission to delete the post.')
		return redirect(url_for('.index'))
	try:
		Comment.query.filter_by(post_id=id).delete()
		db.session.delete(post)
		db.session.commit()
	except IntegrityError:
		db.session.rollback()

	return redirect(url_for('.index'))

#用户资料(页面)
@main.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	posts = user.posts.order_by(Post.timestamp.desc()).all()
	return render_template('user.html', user=user, posts=posts)

#用户个性描述编辑(功能)
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

#头像编辑(页面)
@main.route('/edit_avatar', methods=['GET','POST'])
@login_required
def edit_avatar():
	user = current_user._get_current_object()
	return render_template('/edit_avatar.html', user=user)

#用户头像上传与编辑(功能)
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

#管理员编辑用户资料(页面)
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

#协管管理用户评论(页面)
@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
	page = request.args.get('page', 1, type=int)
	pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
		page, per_page=current_app.config['LOOK_POSTS_PER_PAGE'],
		error_out=False)
	comments = pagination.items
	return render_template('moderate.html', comments=comments, pagination=pagination,
		page=page)
#协管员禁用/启用评论(功能)
@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = False
	db.session.add(comment)
	db.session.commit()
	return redirect(url_for('.moderate', 
		page=request.args.get('page', 1, type=int)))

@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
	comment = Comment.query.get_or_404(id)
	comment.disabled = True
	db.session.add(comment)
	db.session.commit()
	return redirect(url_for('.moderate', 
		page=request.args.get('page', 1, type=int)))	

#关注用户(功能)
@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	if current_user.is_following(user):
		# flash('You are already following this user.')
		return redirect(url_for('.user', username=username))
	current_user.follow(user)
	db.session.commit()
	flash('You are now following %s' % username)
	return redirect(url_for('.user', username=username))
#取消关注(功能)
@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user')
		return redirect(url_for('.index'))
	if not current_user.is_following(user):
		# flash('You are not following this user.')
		return redirect(url_for('.user', username=username))
	current_user.unfollow(user)
	db.session.commit()
	flash('You are not following this user.')
	return redirect(url_for('.user', username=username))

#显示关注用户列表(页面)
@main.route('/followers/<username>')
def followers(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followers.paginate(
		page, per_page=current_app.config['LOOK_POSTS_PER_PAGE'],
		error_out=False)
	follows = [{'user':item.follower, 'timestamp':item.timestamp} \
			   for item in pagination.items]
	return render_template('followers.html', user=user, title='Followers of',
							endpoint='.followers', pagination=pagination,
							follows=follows)

#显示被关注用户列表(页面)
@main.route('/followed_by/<username>')
def followed_by(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = user.followed.paginate(
		page, per_page=current_app.config['LOOK_POSTS_PER_PAGE'],
		error_out=False)
	follows = [{'user':item.followed, 'timestamp':item.timestamp} \
				for item in pagination.items]
	return render_template('followers.html', user=user, title='Followed by',
							endpoint='.followers', pagination=pagination,
							follows=follows)

#首页显示所有文章or关注着的文章(标签)
@main.route('/all')
@login_required
def show_all():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed', '', max_age=30*24*60) #30天
	return resp
@main.route('/followed')
@login_required
def show_followed():
	resp = make_response(redirect(url_for('.index')))
	resp.set_cookie('show_followed', '1', max_age=30*24*60 )
	return resp