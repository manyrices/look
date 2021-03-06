from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from datetime import datetime
from markdown import markdown
import bleach
from app.exceptions import ValidationError


#以二进制叠加方式判断一个用户拥有的权限
class Permission:
	FOLLOW = 1 #关注
	COMMENT = 2 #评论
	WRITE = 4 #发布
	MODERATE = 8 #协管
	ADMIN = 16 #管理员

#用户关注类(自引用关联)
class Follow(db.Model):
	__tablename__ = 'follows'
	follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
							primary_key=True)
	followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
							primary_key=True)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)

#用户类
class User(db.Model, UserMixin):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(64), unique=True, index=True)
	username = db.Column(db.String(64), unique=True)
	password_hash = db.Column(db.String(128))
	confirmed = db.Column(db.Boolean, default=False)
	role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
	posts = db.relationship('Post', backref='author',lazy='dynamic')
	comments = db.relationship('Comment', backref='author', lazy='dynamic')
	#用户信息字段
	avatar = db.Column(db.String(128), default='default_avatar.jpg')
	about_me = db.Column(db.Text(), default='The user is lazy, there is nothing left.')
	member_since = db.Column(db.DateTime(), default=datetime.utcnow)
	last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
	#关注字段(自引用多对多关系实现)
	#self--->user
	followed = db.relationship('Follow',
							   foreign_keys=[Follow.follower_id],
							   backref=db.backref('follower', lazy='joined'),
							   lazy='dynamic',
							   cascade='all, delete-orphan')
	#user--->self
	followers = db.relationship('Follow',
							   foreign_keys=[Follow.followed_id],
							   backref=db.backref('followed', lazy='joined'),
							   lazy='dynamic',
							   cascade='all, delete-orphan')
	def follow(self, user):
		if not self.is_following(user):
			f = Follow(follower=self, followed=user)
			db.session.add(f)
	def unfollow(self, user):
		f = self.followed.filter_by(followed_id=user.id).first()
		if f:
			db.session.delete(f)
	def is_following(self, user):
		if user.id is None:
			return False
		return self.followed.filter_by(followed_id=user.id).first() is not None
	def is_followed_by(self, user):
		if user.id is None:
			return False
		return self.followers.filter_by(follower_id=user.id).first() is not None

	@property
	def followed_posts(self):
		return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
				.filter(Follow.follower_id == self.id)
	

	@property
	def password(self):
		raise AttributeError('password is not a readable attribute')
	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)
	
	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

	def generate_confirmation_token(self, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'confirm': self.id}).decode('utf-8')

	def confirm(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token.encode('utf-8'))
		except:
			return False
		if data.get('confirm') != self.id:
			return False
		self.confirmed = True
		db.session.add(self)
		return True

	def generate_reset_token(self, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'reset':self.id}).decode('utf-8')

	def generate_change_email_token(self, email, expiration=3600):
		s = Serializer(current_app.config['SECRET_KEY'], expiration)
		return s.dumps({'email':email,'change_email_id':self.id}).decode('utf-8')

	def change_email(self, token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token.encode('utf-8'))
		except:
			return False
		if data.get('change_email_id') != self.id:
			return False
		new_email = data.get('email')
		if new_email is None:
			return False
		if self.query.filter_by(email=new_email).first():
			return False

		self.email = new_email
		db.session.add(self)
		return True

	@staticmethod
	def reset_password(token, new_password):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token.encode('utf-8'))
		except:
			return False
		user = User.query.get(data.get('reset'))
		if user is None:
			return False
		user.password = new_password
		db.session.add(user)
		return True

	#------------api-------------

	def to_json(self):
		json_user = {
			'url': url_for('api.get_user', id=self.id),
			'username': self.username,
			'avatar': self.avatar,
			'member_since': self.member_since,
			'last_seen': self.last_seen,
			'posts_url': url_for('api.get_user_posts', id=self.id),
			'followed_posts_url': url_for('api.get_user_followed_posts', 
										id=self.id),
			'post_count': self.posts.count()
		}
		return json_user

	def generate_auth_token(self, expiration):
		s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
		return s.dumps({'id': self.id}).decode('utf-8')

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(current_app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except:
			return None
		return User.query.get(data['id'])
	
	#------------endapi-------------	

	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
		self.follow(self)
		if self.role is None:
			if self.email == current_app.config['LOOK_ADMIN']:
				self.role = Role.query.filter_by(name='Administrator').first()
			if self.role is None:
				self.role = Role.query.filter_by(default=True).first()

	#检查用户是否有指定的权限
	def can(self, perm):
		return self.role is not None and self.role.has_permission(perm)
	def is_administrator(self):
		return self.can(Permission.ADMIN)

	#用于刷新用户最后的访问时间
	def ping(self):
		self.last_seen = datetime.utcnow()
		db.session.add(self)
		db.session.commit()

#角色类,赋予不同角色不同的功能
class Role(db.Model):
	__tablename__ = 'roles'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64))
	default = db.Column(db.Boolean, default=False, index=True)
	permissions = db.Column(db.Integer)
	users = db.relationship('User', backref='role', lazy='dynamic')

	#角色类的构造函数，实例化角色类初始化角色权限值为0
	def __init__(self, **kwargs):
		super(Role, self).__init__(**kwargs)
		if self.permissions is None:
			self.permissions = 0

	def has_permission(self, perm):
		return self.permissions & perm == perm
	def add_permission(self, perm):
		if not self.has_permission(perm):
			self.permissions += perm
	def remove_permission(self, perm):
		if self.has_permission(perm):
			self.permissions -= perm
	def reset_permission(self):
		self.permissions = 0

	@staticmethod
	def insert_roles():
		roles = {
			'User':[Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
			'Moderator':[Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, 
						Permission.MODERATE],
			'Administrator':[Permission.FOLLOW, Permission.COMMENT, Permission.WRITE,
					 Permission.MODERATE, Permission.ADMIN],
		}
		default_role = 'User'
		for r in roles:
			role = Role.query.filter_by(name=r).first()
			if role is None:
				role = Role(name=r)
			role.reset_permission()
			for perm in roles[r]:
				role.add_permission(perm)
			role.default = (role.name == default_role)
			db.session.add(role)
		db.session.commit()

#文章类
class Post(db.Model):
	__tablename__ = 'posts'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text) #用于富文本转换后缓存HTML代码
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	comments = db.relationship('Comment', backref='post', lazy='dynamic')

	#---------------api---------------

	def to_json(self):
		json_post = {
			'url': url_for('api.get_post', id=self.id),
			'body': self.body,
			'body_html': self.body_html,
			'timestamp': self.timestamp,
			'author_url': url_for('api.get_user', id=self.author_id),
			'comments_url': url_for('api.get_post_comments', id=self.id),
			'comment_count': self.comments.count()	
		}
		return json_post

	@staticmethod
	def from_json(json_post):
		body = json_post.get('body')
		if body is None or body == '':
			raise ValidationError('post does not have a body')
		return Post(body=body)

	#--------------endapi---------------

	@staticmethod
	def on_change_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
						'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
						'h1', 'h2', 'h3', 'p']
		target.body_html = bleach.linkify(bleach.clean(
			markdown(value, output_format='html'),
			tags=allowed_tags, strip=True))

db.event.listen(Post.body, 'set', Post.on_change_body)

#评论类
class Comment(db.Model):
	__tablename__ = 'comments'
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text)
	body_html = db.Column(db.Text)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	disabled = db.Column(db.Boolean)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

	#----------------api----------------

	def to_json(self):
		json_comment = {
			'url': url_for('api.get_comment', id=self.id),
			'post_url': url_for('api.get_post', id=self.post_id),
			'body': self.body,
			'body_html': self.body_html,
			'timestamp': self.timestamp,
			'author_url': url_for('api.get_user', id=self.author_id),
		}
		return json_comment

	@staticmethod
	def from_json(json_comment):
		body = json_comment.get('body')
		if body is None or body == '':
			raise ValidationError('comment does not have a body')
		return Comment(body=body)

	#--------------endapi----------------


	@staticmethod
	def on_changed_body(target, value, oldvalue, initiator):
		allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i', 'strong']
		target.body_html = bleach.linkify(bleach.clean(
			markdown(value, output_format='html'),
			tags=allowed_tags, strip=True))

db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class AnonymousUser(AnonymousUserMixin):
	def can(self, permissions):
		return False
	def is_administrator(self):
		return False


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

login_manager.anonymous_user = AnonymousUser