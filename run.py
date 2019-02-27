from app import create_app, db
from flask_migrate import Migrate

app = create_app('default')
migrate = Migrate(app, db)
from app.models import User

@app.shell_context_processor
def make_shell_context():
	return dict(db=db, User=User)