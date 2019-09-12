from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from celery import Celery

from app.flask_celery import make_celery

# Initialize Flask
app = Flask(__name__)

# Load the configuration
app.config.from_object('app.config.default')
app.config.from_envvar("OGN_CONFIG_MODULE", silent=True)

# Initialize other things
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
cache = Cache(app)
celery = make_celery(app)

from app.main import bp as bp_main
app.register_blueprint(bp_main)

from app import commands
