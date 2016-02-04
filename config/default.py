SQLALCHEMY_DATABASE_URI = 'sqlite:///beacons.db'

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'


from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'update-ddb': {
        'task': 'ogn.collect.database.import_ddb',
        'schedule': timedelta(minutes=15),
    },
    'update-receiver-distance': {
        'task': 'ogn.collect.heatmap.update_beacon_receiver_distance_all',
        'schedule': timedelta(minutes=5),
    },
# Only supported with postgresql backend
#    'update-logbook': {
#        'task': 'ogn.collect.logbook.compute_takeoff_and_landing',
#        'schedule': timedelta(minutes=15),
#    },
#    'update-receiver-table': {
#        'task': 'ogn.collect.receiver.update_receivers',
#        'schedule': timedelta(minutes=5),
#    },
}

CELERY_TIMEZONE = 'UTC'
