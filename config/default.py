SQLALCHEMY_DATABASE_URI = 'sqlite:///beacons.db'

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'


from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'update-receiver-distance': {
        'task': 'ogn.collect.heatmap.update_beacon_receiver_distance_all',
        'schedule': timedelta(minutes=5),
    },
}

CELERY_TIMEZONE = 'UTC'
