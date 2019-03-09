import os
import importlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from celery import Celery
from celery.signals import worker_init, worker_shutdown

os.environ.setdefault('OGN_CONFIG_MODULE', 'config.default')
config = importlib.import_module(os.environ['OGN_CONFIG_MODULE'])


@worker_init.connect
def connect_db(sender=None, headers=None, body=None, **kwargs):
    # Load settings like DB_URI...
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=False)

    Session = sessionmaker(bind=engine)
    sender.app.session = Session()


@worker_shutdown.connect
def close_db(sender=None, headers=None, body=None, **kwargs):
    sender.app.session.close()


app = Celery('ogn_python.collect',
             backend='amqp://',
             include=["ogn_python.collect.database",
                      "ogn_python.collect.logbook",
                      "ogn_python.collect.stats",
                      "ogn_python.collect.takeoff_landings",
                      "ogn_python.collect.ognrange"
                      ])

app.config_from_envvar("OGN_CONFIG_MODULE")
