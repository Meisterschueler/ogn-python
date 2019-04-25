SECRET_KEY = 'i-like-ogn'

SQLALCHEMY_DATABASE_URI = 'postgresql://ogn:ognwriter@localhost:5432/ogn'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-Cache stuff
CACHE_TYPE = 'redis'
CACHE_DEFAULT_TIMEOUT = 300

# Celery stuff
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'


from celery.schedules import crontab
from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'update-ddb': {
        'task': 'import_ddb',
        'schedule': timedelta(hours=1),
    },
    'update-country-codes': {
        'task': 'update_receivers_country_code',
        'schedule': timedelta(days=1),
    },
    'update-takeoff-and-landing': {
        'task': 'update_takeoff_landings',
        'schedule': timedelta(hours=1),
        'kwargs': {'last_minutes': 90},
    },
    'update-logbook': {
        'task': 'update_logbook_entries',
        'schedule': timedelta(hours=2),
    },
    'update-max-altitudes': {
        'task': 'update_logbook_max_altitude',
        'schedule': timedelta(hours=1),
    },
    'update-stats-daily': {
        'task': 'update_stats',
        'schedule': crontab(hour=0, minute=5),
        'kwargs': {'day_offset': -1},
    },
    'purge_old_data': {
        'task': 'purge_old_data',
        'schedule': timedelta(hours=1),
        'kwargs': {'max_hours': 48}
    },
}
