import os 

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
	SECRET_KEY = os.urandom(24)
	SQLALCHEMY_TRACK_MODIFICATIONS = False

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