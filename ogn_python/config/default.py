SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@localhost:5432/ogn'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Celery stuff
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'


from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'update-ddb': {
        'task': 'import_ddb',
        'schedule': timedelta(minutes=1),
    },
    'update-country-codes': {
        'task': 'update_receivers_country_code',
        'schedule': timedelta(minutes=1),
    },
    'update-takeoff-and-landing': {
        'task': 'update_takeoff_landings',
        'schedule': timedelta(minutes=1),
    },
    'update-logbook': {
        'task': 'update_logbook_entries',
        'schedule': timedelta(minutes=1),
    },
    'update-max-altitudes': {
        'task': 'update_logbook_max_altitude',
        'schedule': timedelta(minutes=1),
    },
}
