from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from celery import Celery

from ogn_python.navigation import nav
from ogn_python.flask_celery import make_celery

# Initialize Flask
app = Flask(__name__)

# Load the configuration
#app.config.from_object('config.default')
app.config.from_envvar('OGN_CONFIG_MODULE')

# Bootstrap
bootstrap = Bootstrap(app)

# Sqlalchemy
db = SQLAlchemy(app)

# Cache
cache = Cache(app)

# Celery
celery = make_celery(app)

# Navigation
nav.init_app(app)
