from datetime import datetime

from celery.utils.log import get_task_logger

from sqlalchemy import insert, distinct
from sqlalchemy.sql import null, and_, func, or_, update
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
        .filter(and_(func.date(AircraftBeacon.timestamp) == date, AircraftBeacon.device_id != null())) \
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
def update_receiver_stats(session=None, date=None):
    """Add/update receiver stats."""

    if session is None:
        session = app.session

    if not date:
        logger.warn("A date is needed for calculating stats. Exiting")
        return None

    # First kill the stats for the selected date
    deleted_counter = session.query(ReceiverStats) \
        .filter(ReceiverStats.date == date) \
        .delete()

    # Calculate stats, firstseen, lastseen and last values != NULL
    receiver_stats = session.query(
            distinct(ReceiverBeacon.receiver_id).label('receiver_id'),
            func.date(ReceiverBeacon.timestamp).label('date'),
            func.first_value(ReceiverBeacon.timestamp)
                .over(partition_by=ReceiverBeacon.receiver_id, order_by=case([(ReceiverBeacon.timestamp == null(), None)], else_=ReceiverBeacon.timestamp).asc().nullslast())
                .label('firstseen'),
            func.first_value(ReceiverBeacon.timestamp)
                .over(partition_by=ReceiverBeacon.receiver_id, order_by=case([(ReceiverBeacon.timestamp == null(), None)], else_=ReceiverBeacon.timestamp).desc().nullslast())
                .label('lastseen'),
            func.first_value(ReceiverBeacon.location_wkt)
                .over(partition_by=ReceiverBeacon.receiver_id, order_by=case([(ReceiverBeacon.location_wkt == null(), None)], else_=ReceiverBeacon.timestamp).desc().nullslast())
                .label('location_wkt'),
            func.first_value(ReceiverBeacon.altitude)
                .over(partition_by=ReceiverBeacon.receiver_id, order_by=case([(ReceiverBeacon.altitude == null(), None)], else_=ReceiverBeacon.timestamp).desc().nullslast())
                .label('altitude'),
            func.first_value(ReceiverBeacon.version)
                .over(partition_by=ReceiverBeacon.receiver_id, order_by=case([(ReceiverBeacon.version == null(), None)], else_=ReceiverBeacon.timestamp).desc().nullslast())
                .label('version'),
            func.first_value(ReceiverBeacon.platform)
                .over(partition_by=ReceiverBeacon.receiver_id, order_by=case([(ReceiverBeacon.platform == null(), None)], else_=ReceiverBeacon.timestamp).desc().nullslast())
                .label('platform')) \
        .subquery()

    # And insert them
    ins = insert(ReceiverStats).from_select(
        [ReceiverStats.receiver_id, ReceiverStats.date, ReceiverStats.firstseen, ReceiverStats.lastseen, ReceiverStats.location_wkt, ReceiverStats.altitude, ReceiverStats.version, ReceiverStats.platform],
        receiver_stats)
    res = session.execute(ins)
    insert_counter = res.rowcount
    session.commit()
    logger.warn("ReceiverStats for {}: {} deleted, {} inserted".format(date, deleted_counter, insert_counter))

    # Update AircraftBeacon distances
    upd = update(AircraftBeacon) \
        .where(and_(func.date(AircraftBeacon.timestamp) == ReceiverStats.date,
                    AircraftBeacon.receiver_id == ReceiverStats.receiver_id,
                    AircraftBeacon.distance == null())) \
        .values({"distance": func.ST_Distance_Sphere(AircraftBeacon.location_wkt, ReceiverStats.location_wkt)})

    result = session.execute(upd)
    update_counter = result.rowcount
    session.commit()
    logger.warn("Updated {} AircraftBeacons".format(update_counter))

    return "ReceiverStats for {}: {} deleted, {} inserted, AircraftBeacons: {} updated".format(date, deleted_counter, insert_counter, update_counter)
