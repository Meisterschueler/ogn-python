SQLALCHEMY_DATABASE_URI = 'sqlite:///beacons.db'

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
