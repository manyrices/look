import os 

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY',os.urandom(24))
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.163.com')
	MAIL_PORT = int(os.environ.get('MAIL_PORT', '25'))
	MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
	MAIL_USERNAME = os.environ.get('MAIL_USERNAME','look_everything@163.com')
	MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD','qwer1234')
	LOOK_MAIL_SUBJECT_PREFIX = '[Rice]'
	LOOK_MAIL_SENDER = 'see see <look_everything@163.com>'

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

