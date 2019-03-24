from flask import Flask 
from flask_bootstrap import Bootstrap
from config import config
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment 
#文章富文本支持
#PageDown 使用javascript实现的客户端Markdown到HTML转换程序
#Flask-PageDown 为flask包装的PageDown，把PageDown集成到Flask-WTF表单中
#Markdown 使用python实现的服务器端Markdown到HTML转换程序
#Bleach 使用Python实现的HTML清理程序
from flask_pagedown import PageDown

bootstrap = Bootstrap()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()
moment = Moment()
pagedown = PageDown()

def create_app(config_name):
	app = Flask(__name__)

	app.config.from_object(config[config_name])
	config[config_name].init_app(app)
	
	bootstrap.init_app(app)
	db.init_app(app)
	login_manager.init_app(app)
	mail.init_app(app)
	moment.init_app(app)
	pagedown.init_app(app)
	
	from .main import main as main_blueprint
	app.register_blueprint(main_blueprint)
	from .auth import auth as auth_blueprint
	app.register_blueprint(auth_blueprint, url_prefix='/auth')

	return app 

