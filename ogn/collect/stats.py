from datetime import datetime

from celery.utils.log import get_task_logger

from sqlalchemy import insert, distinct
from sqlalchemy.sql import null, and_, func, or_
from sqlalchemy.sql.expression import literal_column, case

from ogn.model import AircraftBeacon, DeviceStats, ReceiverStats

from .celery import app
from ogn.model.receiver_beacon import ReceiverBeacon

logger = get_task_logger(__name__)


@app.task
def update_device_stats(session=None, date=None):
    """Add/update device stats."""

    if session is None:
        session = app.session

    if not date:
        logger.warn("A date is needed for calculating stats. Exiting")
        return None

    # First kill the stats for the selected date
    deleted_counter = session.query(DeviceStats) \
        .filter(DeviceStats.date == date) \
        .delete()

    # Since "distinct count" does not work in window functions we need a work-around for receiver counting
    sq = session.query(AircraftBeacon,
            func.dense_rank()
                .over(partition_by=AircraftBeacon.device_id, order_by=AircraftBeacon.receiver_id)
                .label('dr')) \
        .filter(and_(AircraftBeacon.device_id != null(), func.date(AircraftBeacon.timestamp) == date)) \
        .filter(or_(AircraftBeacon.error_count == 0, AircraftBeacon.error_count == null())) \
        .subquery()

    # Calculate stats, firstseen, lastseen and last values != NULL
    device_stats = session.query(
            distinct(sq.c.device_id).label('device_id'),
            func.date(sq.c.timestamp).label('date'),
            func.max(sq.c.dr)
                .over(partition_by=sq.c.device_id)
                .label('receiver_count'),
            func.max(sq.c.altitude)
                .over(partition_by=sq.c.device_id)
                .label('max_altitude'),
            func.count(sq.c.id)
                .over(partition_by=sq.c.device_id)
                .label('aircraft_beacon_count'),
            func.first_value(sq.c.timestamp)
                .over(partition_by=sq.c.device_id, order_by=case([(sq.c.timestamp == null(), None)], else_=sq.c.timestamp).asc().nullslast())
                .label('firstseen'),
            func.first_value(sq.c.timestamp)
                .over(partition_by=sq.c.device_id, order_by=case([(sq.c.timestamp == null(), None)], else_=sq.c.timestamp).desc().nullslast())
                .label('lastseen'),
            func.first_value(sq.c.aircraft_type)
                .over(partition_by=sq.c.device_id, order_by=case([(sq.c.aircraft_type == null(), None)], else_=sq.c.timestamp).desc().nullslast())
                .label('aircraft_type'),
            func.first_value(sq.c.stealth)
                .over(partition_by=sq.c.device_id, order_by=case([(sq.c.stealth == null(), None)], else_=sq.c.timestamp).desc().nullslast())
                .label('stealth'),
            func.first_value(sq.c.software_version)
                .over(partition_by=sq.c.device_id, order_by=case([(sq.c.software_version == null(), None)], else_=sq.c.timestamp).desc().nullslast())
                .label('software_version'),
            func.first_value(sq.c.hardware_version)
                .over(partition_by=sq.c.device_id, order_by=case([(sq.c.hardware_version == null(), None)], else_=sq.c.timestamp).desc().nullslast())
                .label('hardware_version'),
            func.first_value(sq.c.real_address)
                .over(partition_by=sq.c.device_id, order_by=case([(sq.c.real_address == null(), None)], else_=sq.c.timestamp).desc().nullslast())
                .label('real_address')) \
        .subquery()

    # And insert them
    ins = insert(DeviceStats).from_select(
        [DeviceStats.device_id, DeviceStats.date, DeviceStats.receiver_count, DeviceStats.max_altitude, DeviceStats.aircraft_beacon_count, DeviceStats.firstseen, DeviceStats.lastseen, DeviceStats.aircraft_type, DeviceStats.stealth,
         DeviceStats.software_version, DeviceStats.hardware_version, DeviceStats.real_address],
        device_stats)
    res = session.execute(ins)
    insert_counter = res.rowcount
    session.commit()
    logger.debug("DeviceStats for {}: {} deleted, {} inserted".format(date, deleted_counter, insert_counter))

    return "DeviceStats for {}: {} deleted, {} inserted".format(date, deleted_counter, insert_counter)


@app.task
def update_receiver_stats(date=None):
    """Add/update receiver stats."""

    if not date:
        logger.warn("A date is needed for calculating stats. Exiting")
        return None

    # First kill the stats for the selected date
    deleted_counter = session.query(ReceiverStats) \
        .filter(ReceiverStats.date == date) \
        .delete()

    # Calculate stats for the selected date
    receiver_stats = session.query(
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
    res = session.execute(ins)
    insert_counter = res.rowcount
    session.commit()
    logger.debug("ReceiverStats for {}: {} deleted, {} inserted".format(date, deleted_counter, insert_counter))

    return "ReceiverStats for {}: {} deleted, {} inserted".format(date, deleted_counter, insert_counter)
