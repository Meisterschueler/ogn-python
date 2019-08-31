SQLALCHEMY_DATABASE_URI = "postgresql://postgres@localhost:5432/ogn_test"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Celery stuff
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
