from celery.utils.log import get_task_logger

from sqlalchemy import insert, distinct
from sqlalchemy.sql import null, and_, func
from sqlalchemy.sql.expression import literal_column

from ogn.model import AircraftBeacon, DeviceStats, ReceiverStats

from .celery import app

logger = get_task_logger(__name__)


@app.task
def update_device_stats(date=None):
    """Add/update entries in device stats table."""

    if not date:
        logger.warn("A date is needed for calculating stats. Exiting")
        return None

    # First kill the stats for the selected date
    deleted_counter = app.session.query(DeviceStats) \
        .filter(DeviceStats.date == date) \
        .delete()

    # Calculate stats for the selected date
    device_stats = app.session.query(
        AircraftBeacon.device_id,
        func.date(AircraftBeacon.timestamp).label('date'),
        func.count(distinct(AircraftBeacon.receiver_id)).label('receiver_count'),
        func.count(AircraftBeacon.id).label('aircraft_beacon_count'),
        func.max(AircraftBeacon.altitude).label('max_altitude')) \
        .filter(and_(AircraftBeacon.device_id != null(), AircraftBeacon.receiver_id != null())) \
        .filter(func.date(AircraftBeacon.timestamp) == date) \
        .group_by(AircraftBeacon.device_id, func.date(AircraftBeacon.timestamp)) \
        .subquery()

    # And insert them
    ins = insert(DeviceStats).from_select(
        [DeviceStats.device_id, DeviceStats.date, DeviceStats.receiver_count, DeviceStats.aircraft_beacon_count, DeviceStats.max_altitude],
        device_stats)
    res = app.session.execute(ins)
    insert_counter = res.rowcount
    app.session.commit()
    logger.debug("DeviceStats entries for {}: {} deleted, {} inserted".format(date, deleted_counter, insert_counter))

    return "DeviceStats entries for {}: {} deleted, {} inserted".format(date, deleted_counter, insert_counter)


@app.task
def update_receiver_stats(date=None):
    """Add/update entries in receiver stats table."""

    if not date:
        logger.warn("A date is needed for calculating stats. Exiting")
        return None

    # First kill the stats for the selected date
    deleted_counter = app.session.query(ReceiverStats) \
        .filter(ReceiverStats.date == date) \
        .delete()

    # Calculate stats for the selected date
    receiver_stats = app.session.query(
        AircraftBeacon.receiver_id,
        literal_column("'{}'".format(date)).label('date'),
        func.count(AircraftBeacon.id).label('aircraft_beacon_count'),
        func.count(distinct(AircraftBeacon.device_id)).label('aircraft_count'),
        func.max(AircraftBeacon.distance).label('max_distance')) \
        .filter(AircraftBeacon.receiver_id != null()) \
        .filter(func.date(AircraftBeacon.timestamp) == date) \
        .group_by(AircraftBeacon.receiver_id) \
        .subquery()

    # And insert them
    ins = insert(ReceiverStats).from_select(
        [ReceiverStats.receiver_id, ReceiverStats.date, ReceiverStats.aircraft_beacon_count, ReceiverStats.aircraft_count, ReceiverStats.max_distance],
        receiver_stats)
    res = app.session.execute(ins)
    insert_counter = res.rowcount
    app.session.commit()
    logger.debug("ReceiverStats entries for {}: {} deleted, {} inserted".format(date, deleted_counter, insert_counter))

    return "ReceiverStats entries for {}: {} deleted, {} inserted".format(date, deleted_counter, insert_counter)
