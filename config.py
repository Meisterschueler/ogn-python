import os


class BaseConfig:
    SECRET_KEY = "i-like-ogn"

    # Flask-Cache stuff
    CACHE_TYPE = "redis"
    CACHE_DEFAULT_TIMEOUT = 300

    # Redis stuff
    REDIS_URL = "redis://localhost:6379/0"

    # Celery stuff
    BROKER_URL = os.environ.get("BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)

    APRS_USER = "OGNPYTHON"

    # Upload configuration
    MAX_CONTENT_LENGTH = 1024 * 1024    # max. 1MB
    UPLOAD_EXTENSIONS = ['.csv']
    UPLOAD_PATH = 'uploads'


class DefaultConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/ogn")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Celery beat stuff
    from celery.schedules import crontab
    from datetime import timedelta

    CELERYBEAT_SCHEDULE = {
        "transfer_to_database": {"task": "transfer_to_database", "schedule": timedelta(minutes=1)},
        "update_statistics": {"task": "update_statistics", "schedule": timedelta(minutes=5)},
        "update_takeoff_landings": {"task": "update_takeoff_landings", "schedule": timedelta(minutes=1), "kwargs": {"last_minutes": 20}},
        "update_logbook": {"task": "update_logbook", "schedule": timedelta(minutes=1)},
        "update_logbook_previous_day": {"task": "update_logbook", "schedule": crontab(hour=1, minute=0), "kwargs": {"day_offset": -1}},

        "update_ddb_daily": {"task": "import_ddb", "schedule": timedelta(days=1)},
        #"update_logbook_max_altitude": {"task": "update_logbook_max_altitude", "schedule": timedelta(minutes=1), "kwargs": {"offset_days": 0}},

        #"purge_old_data": {"task": "purge_old_data", "schedule": timedelta(hours=1), "kwargs": {"max_hours": 48}},
    }

    FLASK_PROFILER = {
        "enabled": True,
        "storage": {
            "engine": "sqlalchemy",
            "db_url": SQLALCHEMY_DATABASE_URI
        },
        "ignore": [
            "^/static/.*"
        ]
    }


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432/ogn_test"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False


configs = {
    'default': DefaultConfig,
    'development': DevelopmentConfig,
    'testing': DevelopmentConfig
}
