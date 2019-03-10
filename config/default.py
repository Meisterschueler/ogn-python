SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@localhost:5432/ogn'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Celery stuff
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'


from datetime import timedelta

beat_schedule = {
    'update-ddb': {
        'task': 'ogn_python.collect.celery.import_ddb',
        'schedule': timedelta(minutes=15),
    },
    'update-country-codes': {
        'task': 'ogn_python.collect.celery.update_receivers_country_code',
        'schedule': timedelta(minutes=5),
    },
    'update-takeoff-and-landing': {
        'task': 'ogn_python.collect.celery.update_takeoff_landings',
        'schedule': timedelta(minutes=15),
    },
    'update-logbook': {
        'task': 'ogn_python.collect.celery.update_logbook_entries',
        'schedule': timedelta(minutes=15),
    },
    'update-max-altitudes': {
        'task': 'ogn_python.collect.celery.update_logbook_max_altitude',
        'schedule': timedelta(minutes=15),
    },
}

timezone = 'UTC'
