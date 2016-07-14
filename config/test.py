SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@localhost:5432/ogn_test'

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'


CELERYBEAT_SCHEDULE = {}

CELERY_TIMEZONE = 'UTC'
