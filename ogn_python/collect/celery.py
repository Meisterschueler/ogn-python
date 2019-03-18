import datetime

from celery.utils.log import get_task_logger

from ogn_python.collect.takeoff_landings import update_entries as takeoff_update_entries

from ogn_python.collect.logbook import update_entries as logbook_update_entries
from ogn_python.collect.logbook import update_max_altitudes as logbook_update_max_altitudes

from ogn_python.collect.database import import_ddb as device_infos_import_ddb
from ogn_python.collect.database import update_country_code as receivers_update_country_code

from ogn_python import db
from ogn_python import celery


logger = get_task_logger(__name__)


@celery.task(name='update_takeoff_landings')
def update_takeoff_landings(last_minutes):
    """Compute takeoffs and landings."""

    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(minutes=last_minutes)
    takeoff_update_entries(session=db.session, start=start, end=end, logger=logger)


@celery.task(name='update_logbook_entries')
def update_logbook_entries():
    """Add/update logbook entries."""

    today = datetime.datetime.today()
    logbook_update_entries(session=db.session, date=today, logger=logger)


@celery.task(name='update_logbook_max_altitude')
def update_logbook_max_altitude():
    """Add max altitudes in logbook when flight is complete (takeoff and landing)."""

    logbook_update_max_altitudes(session=db.session, logger=logger)


@celery.task(name='import_ddb')
def import_ddb():
    """Import registered devices from the DDB."""

    device_infos_import_ddb(session=db.session, logger=logger)


@celery.task(name='update_receivers_country_code')
def update_receivers_country_code():
    """Update country code in receivers table if None."""

    receivers_update_country_code(session=db.session, logger=logger)


@celery.task(name='purge_old_data')
def purge_old_data(max_hours):
    """Delete AircraftBeacons and ReceiverBeacons older than given 'age'."""

    from ogn_python.model import AircraftBeacon, ReceiverBeacon
    min_timestamp = datetime.datetime.utcnow() - datetime.timedelta(hours=max_hours)
    db.session(AircraftBeacon) \
        .filter(AircraftBeacon.timestamp < min_timestamp) \
        .delete()

    db.session(ReceiverBeacon) \
        .filter(ReceiverBeacon.timestamp < min_timestamp) \
        .delete()
