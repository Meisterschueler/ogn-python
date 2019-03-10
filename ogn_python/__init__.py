from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from celery import Celery

from ogn_python.navigation import nav
from ogn_python.flask_celery import make_celery

# Initialize Flask
app = Flask(__name__)
app.config.from_object('config.default')

# Bootstrap
bootstrap = Bootstrap(app)

# Sqlalchemy
db = SQLAlchemy(app)

# Celery
celery = make_celery(app)

# Navigation
nav.init_app(app)
