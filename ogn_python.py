import os

from app import create_app, db, commands

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
commands.register(app)

@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db)
