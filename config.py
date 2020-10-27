import os

class BaseConfig:
    SECRET_KEY = "i-like-ogn"
    
    # Flask-Cache stuff
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Redis stuff
    REDIS_URL = "redis://localhost:6379/0"
    
    # Celery stuff
    BROKER_URL = os.environ.get("BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)

    APRS_USER = "OGNPYTHON"

class DefaultConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/ogn")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Celery beat stuff
    from celery.schedules import crontab
    from datetime import timedelta

    CELERYBEAT_SCHEDULE = {
        #"update-ddb": {"task": "import_ddb", "schedule": timedelta(hours=1)},
        #"update-country-codes": {"task": "update_receivers_country_code", "schedule": timedelta(days=1)},
        #"update-takeoff-and-landing": {"task": "update_takeoff_landings", "schedule": timedelta(hours=1), "kwargs": {"last_minutes": 90}},
        #"update-logbook": {"task": "update_logbook_entries", "schedule": timedelta(hours=2), "kwargs": {"day_offset": 0}},
        #"update-max-altitudes": {"task": "update_logbook_max_altitude", "schedule": timedelta(hours=1), "kwargs": {"day_offset": 0}},
        #"update-logbook-daily": {"task": "update_logbook_entries", "schedule": crontab(hour=1, minute=0), "kwargs": {"day_offset": -1}},
        #"purge_old_data": {"task": "purge_old_data", "schedule": timedelta(hours=1), "kwargs": {"max_hours": 48}},
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