SQLALCHEMY_DATABASE_URI = 'postgresql:///ogn'

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'


from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'update-ddb': {
        'task': 'ogn.collect.database.import_ddb',
        'schedule': timedelta(minutes=15),
    },
    'update-device-table': {
        'task': 'ogn.collect.database.update_devices',
        'schedule': timedelta(minutes=5),
    },
    'update-receiver-table': {
        'task': 'ogn.collect.database.update_receivers',
        'schedule': timedelta(minutes=5),
    },
    'update-country-codes': {
        'task': 'ogn.collect.database.update_country_code',
        'schedule': timedelta(minutes=5),
    },
    'update-takeoff-and-landing': {
        'task': 'ogn.collect.takeoff_landings.update_takeoff_landings',
        'schedule': timedelta(minutes=15),
    },
    'update-logbook': {
        'task': 'ogn.collect.logbook.update_logbook',
        'schedule': timedelta(minutes=15),
    },
    'update-max-altitudes': {
        'task': 'ogn.collect.logbook.update_max_altitude',
        'schedule': timedelta(minutes=15),
    },
}

CELERY_TIMEZONE = 'UTC'
