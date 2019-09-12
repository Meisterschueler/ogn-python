import os

from flask_migrate import Migrate
from app import create_app, db
from app.commands import register

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)
register(app)

@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db)