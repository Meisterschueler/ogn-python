from datetime import datetime, timedelta

from app.collect.logbook import update_takeoff_landings as logbook_update_takeoff_landings, update_logbook as logbook_update
from app.collect.logbook import update_max_altitudes as logbook_update_max_altitudes

from app.collect.database import import_ddb as device_infos_import_ddb

from app.collect.gateway import transfer_from_redis_to_database

from app import db, celery

@celery.task(name="transfer_to_database")
def transfer_to_database():
    """Transfer APRS data from Redis to database."""
    
    result = transfer_from_redis_to_database()
    return result
    

@celery.task(name="update_takeoff_landings")
def update_takeoff_landings(last_minutes):
    """Compute takeoffs and landings."""

    end = datetime.utcnow()
    start = end - timedelta(minutes=last_minutes)
    result = logbook_update_takeoff_landings(start=start, end=end)
    return result


@celery.task(name="update_logbook")
def update_logbook(offset_days=None):
    """Add/update logbook entries."""

    result = logbook_update(offset_days=offset_days)
    return result


@celery.task(name="update_logbook_max_altitude")
def update_logbook_max_altitude():
    """Add max altitudes in logbook when flight is complete (takeoff and landing)."""

    result = logbook_update_max_altitudes()
    return result


@celery.task(name="import_ddb")
def import_ddb():
    """Import registered devices from the DDB."""

    result = device_infos_import_ddb()
    return result
