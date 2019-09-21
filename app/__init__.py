from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from celery import Celery

bootstrap = Bootstrap()
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
celery = Celery(__name__, broker='redis://localhost:6379/0')


def create_app(config_name='development'):
    # Initialize Flask
    app = Flask(__name__)

    # Load the configuration
    if config_name == 'testing':
        app.config.from_object('app.config.test')
    else:
        app.config.from_object('app.config.default')
    app.config.from_envvar("OGN_CONFIG_MODULE", silent=True)
    celery.config_from_object(app.config)

    # Initialize other things
    bootstrap.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)

    from app.main import bp as bp_main
    app.register_blueprint(bp_main)

    return app
