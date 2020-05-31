import datetime

from celery.utils.log import get_task_logger

from app.collect.takeoff_landings import update_entries as takeoff_update_entries

from app.collect.logbook import update_entries as logbook_update_entries
from app.collect.logbook import update_max_altitudes as logbook_update_max_altitudes

from app.collect.database import import_ddb as device_infos_import_ddb
from app.collect.database import update_country_code as receivers_update_country_code

from app.collect.ognrange import update_entries as receiver_coverage_update_entries

from app.gateway.bulkimport import DbFeeder

from app import db
from app import redis_client, celery

logger = get_task_logger(__name__)

@celery.task(name="update_takeoff_landings")
def update_takeoff_landings(last_minutes):
    """Compute takeoffs and landings."""

    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(minutes=last_minutes)
    result = takeoff_update_entries(session=db.session, start=start, end=end, logger=logger)
    return result


@celery.task(name="update_logbook_entries")
def update_logbook_entries(day_offset):
    """Add/update logbook entries."""

    date = datetime.datetime.today() + datetime.timedelta(days=day_offset)
    result = logbook_update_entries(session=db.session, date=date, logger=logger)
    return result


@celery.task(name="update_logbook_max_altitude")
def update_logbook_max_altitude(day_offset):
    """Add max altitudes in logbook when flight is complete (takeoff and landing)."""

    date = datetime.datetime.today() + datetime.timedelta(days=day_offset)
    result = logbook_update_max_altitudes(session=db.session, date=date, logger=logger)
    return result


@celery.task(name="import_ddb")
def import_ddb():
    """Import registered devices from the DDB."""

    result = device_infos_import_ddb(session=db.session, logger=logger)
    return result


@celery.task(name="update_receivers_country_code")
def update_receivers_country_code():
    """Update country code in receivers table if None."""

    result = receivers_update_country_code(session=db.session, logger=logger)
    return result


@celery.task(name="purge_old_data")
def purge_old_data(max_hours):
    """Delete AircraftBeacons and ReceiverBeacons older than given 'age'."""

    from app.model import AircraftBeacon, ReceiverBeacon

    min_timestamp = datetime.datetime.utcnow() - datetime.timedelta(hours=max_hours)
    aircraft_beacons_deleted = db.session.query(AircraftBeacon).filter(AircraftBeacon.timestamp < min_timestamp).delete()

    receiver_beacons_deleted = db.session.query(ReceiverBeacon).filter(ReceiverBeacon.timestamp < min_timestamp).delete()

    db.session.commit()

    result = "{} AircraftBeacons deleted, {} ReceiverBeacons deleted".format(aircraft_beacons_deleted, receiver_beacons_deleted)
    return result


@celery.task(name="update_ognrange")
def update_ognrange(day_offset):
    """Create receiver coverage stats for Melissas ognrange."""

    date = datetime.datetime.today() + datetime.timedelta(days=day_offset)

    receiver_coverage_update_entries(session=db.session, date=date)


@celery.task(name="transfer_beacons_to_database")
def transfer_beacons_to_database():
    """Transfer beacons from redis to TimescaleDB."""

    counter = 0
    with DbFeeder() as feeder:
        for key in redis_client.scan_iter(match="ogn-python *"):
            value = redis_client.get(key)
            if value is None:
                redis_client.delete(key)
                continue
            
            reference_timestamp = datetime.datetime.strptime(key[11:].decode('utf-8'), "%Y-%m-%d %H:%M:%S.%f")
            aprs_string = value.decode('utf-8')
            redis_client.delete(key)
            
            feeder.add(aprs_string, reference_timestamp=reference_timestamp)
            counter += 1
    
    return f"Beacons transfered from redis to TimescaleDB: {counter}"
