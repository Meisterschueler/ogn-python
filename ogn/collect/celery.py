from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from celery import Celery
from celery.signals import worker_init, worker_shutdown

app = Celery('ogn.collect',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0',
             include=["ogn.collect.database", "ogn.collect.logbook"])

DB_URI = 'sqlite:///beacons.db'


@worker_init.connect
def connect_db(signal, sender):
    # Load settings like DB_URI...
    engine = create_engine(DB_URI, echo=False)

    Session = sessionmaker(bind=engine)
    sender.app.session = Session()


@worker_shutdown.connect
def close_db(signal, sender):
    sender.app.session.close()


if __name__ == '__main__':
    app.start()
