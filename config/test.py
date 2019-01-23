SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@localhost:5432/ogn_test'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Celery stuff
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'


beat_schedule = {}

timezone = 'UTC'
