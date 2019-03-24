import os 
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY',os.urandom(24))
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.163.com')
	MAIL_PORT = int(os.environ.get('MAIL_PORT', '25'))
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME','look_everything@163.com')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD','******')
	LOOK_MAIL_SUBJECT_PREFIX = '[Rice]'
	LOOK_MAIL_SENDER = 'see see <look_everything@163.com>'
	UPLOAD_FOLDER = basedir + '\\app\\static\\avatar'
	ALLOWED_EXTENSIONS = set(['jpg','jpeg','png','bmp'])
	MAX_CONTENT_LENGTH = 5*1024*1024 #限制上传文件最大容量为5Mb
	LOOK_ADMIN = 'manyrice0o0@gmail.com' #管理员账号
	LOOK_POSTS_PER_PAGE = 20 #设定分页功能中，每一页显示的数目
	
	@staticmethod
	def init_app(app):
		pass


class DevelopmentConfig(Config):
	DEBUG = True
	HOST = '127.0.0.1'
	PORT = '3306'
	DATABASE = 'developlook'
	USERNAME = 'root'
	PASSWORD = 'lanwenbin'
	SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'. \
							format(USERNAME,PASSWORD,HOST,PORT,DATABASE)

class TestingConfig(Config):
	pass

class ProductionConfig(Config):
	pass

config = {
	'development': DevelopmentConfig,
	'testing':TestingConfig,
	'production':ProductionConfig,

	'default': DevelopmentConfig
}

