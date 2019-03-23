from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from datetime import datetime

#以二进制叠加方式判断一个用户拥有的权限
class Permission:
	FOLLOW = 1 #关注
	COMMENT = 2 #评论
	WRITE = 4 #发布
	MODERATE = 8 #协管
	ADMIN = 16 #管理员

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
	#用户信息字段
	avatar = db.Column(db.String(128), default='default_avatar.jpg')
	about_me = db.Column(db.Text(), default='The user is lazy, there is nothing left.')
	member_since = db.Column(db.DateTime(), default=datetime.utcnow)
	last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
	
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

	def __init__(self, **kwargs):
		super(User, self).__init__(**kwargs)
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
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class AnonymousUser(AnonymousUserMixin):
	def can(self, permissions):
		return False
	def is_administrator(self):
		return False


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

login_manager.anonymous_user = AnonymousUser