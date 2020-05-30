from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from celery import Celery
from flask_redis import FlaskRedis

from config import configs

bootstrap = Bootstrap()
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
redis_client = FlaskRedis()
celery = Celery()


def create_app(config_name='default'):
    # Initialize Flask
    app = Flask(__name__)

    # Load the configuration
    configuration = configs[config_name]
    app.config.from_object(configuration)
    app.config.from_envvar("OGN_CONFIG_MODULE", silent=True)
    
    # Initialize other things
    bootstrap.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    redis_client.init_app(app)
    
    init_celery(app)
    
    from app.main import bp as bp_main
    app.register_blueprint(bp_main)

    return app

def init_celery(app):
    celery.conf.broker_url = app.config['CELERY_BROKER_URL']
    celery.conf.result_backend = app.config['CELERY_RESULT_BACKEND']
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Do we need this? Otherwise I cant the celery worker run...
app = create_app()
from app.gateway.bulkimport import DbFeeder
from app.collect.celery_tasks import *