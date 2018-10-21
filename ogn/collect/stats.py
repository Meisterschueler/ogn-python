from datetime import datetime

from celery.utils.log import get_task_logger

from sqlalchemy import insert, distinct
from sqlalchemy.sql import null, and_, func, or_, update
from sqlalchemy.sql.expression import literal_column, case

from ogn.model import AircraftBeacon, DeviceStats, ReceiverStats, RelationStats, Receiver, Device

from .celery import app
from ogn.model.receiver_beacon import ReceiverBeacon

logger = get_task_logger(__name__)


@app.task
def create_device_stats(session=None, date=None):
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
def create_receiver_stats(session=None, date=None):
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

    # Select one day
    sq = session.query(ReceiverBeacon) \
        .filter(func.date(ReceiverBeacon.timestamp) == date) \
        .subquery()

    # Calculate stats, firstseen, lastseen and last values != NULL
    receiver_stats = session.query(
            distinct(sq.c.receiver_id).label('receiver_id'),
            func.date(sq.c.timestamp).label('date'),
            func.first_value(sq.c.timestamp)
                .over(partition_by=sq.c.receiver_id, order_by=case([(sq.c.timestamp == null(), None)], else_=sq.c.timestamp).asc().nullslast())
                .label('firstseen'),
            func.first_value(sq.c.timestamp)
                .over(partition_by=sq.c.receiver_id, order_by=case([(sq.c.timestamp == null(), None)], else_=sq.c.timestamp).desc().nullslast())
                .label('lastseen'),
            func.first_value(sq.c.location)
                .over(partition_by=sq.c.receiver_id, order_by=case([(sq.c.location == null(), None)], else_=sq.c.timestamp).desc().nullslast())
                .label('location_wkt'),
            func.first_value(sq.c.altitude)
                .over(partition_by=sq.c.receiver_id, order_by=case([(sq.c.altitude == null(), None)], else_=sq.c.timestamp).desc().nullslast())
                .label('altitude'),
            func.first_value(sq.c.version)
                .over(partition_by=sq.c.receiver_id, order_by=case([(sq.c.version == null(), None)], else_=sq.c.timestamp).desc().nullslast())
                .label('version'),
            func.first_value(sq.c.platform)
                .over(partition_by=sq.c.receiver_id, order_by=case([(sq.c.platform == null(), None)], else_=sq.c.timestamp).desc().nullslast())
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

    # Update aircraft_beacon_count, aircraft_count and max_distance (without any error and max quality of 36dB@10km which is enough for 640km ... )
    aircraft_beacon_stats = session.query(func.date(AircraftBeacon.timestamp).label('date'),
                                          AircraftBeacon.receiver_id,
                                          func.count(AircraftBeacon.id).label('aircraft_beacon_count'),
                                          func.count(func.distinct(AircraftBeacon.device_id)).label('aircraft_count'),
                                          func.max(AircraftBeacon.distance).label('max_distance')) \
        .filter(and_(func.date(AircraftBeacon.timestamp) == date,
                     AircraftBeacon.error_count == 0,
                     AircraftBeacon.quality <= 40)) \
        .group_by(func.date(AircraftBeacon.timestamp),
                  AircraftBeacon.receiver_id) \
        .subquery()
    
    upd = update(ReceiverStats) \
        .where(and_(ReceiverStats.date == aircraft_beacon_stats.c.date,
                    ReceiverStats.receiver_id == aircraft_beacon_stats.c.receiver_id)) \
        .values({'aircraft_beacon_count': aircraft_beacon_stats.c.aircraft_beacon_count,
                 'aircraft_count': aircraft_beacon_stats.c.aircraft_count,
                 'max_distance': aircraft_beacon_stats.c.max_distance})
        
    result = session.execute(upd)
    update_counter = result.rowcount
    session.commit()
    logger.warn("Updated {} ReceiverStats".format(update_counter)) 

    return "ReceiverStats for {}: {} deleted, {} inserted, {} updated".format(date, deleted_counter, insert_counter, update_counter)


@app.task
def update_device_stats_jumps(session=None, date=None):
    """Update device stats jumps."""

    if session is None:
        session = app.session

    if not date:
        logger.warn("A date is needed for calculating device stats jumps. Exiting")
        return None

    sq = session.query(AircraftBeacon.device_id,
                       AircraftBeacon.timestamp.label('t0'),
                       func.lead(AircraftBeacon.timestamp).over(partition_by=AircraftBeacon.device_id, order_by=AircraftBeacon.timestamp).label('t1'),
                       AircraftBeacon.location_wkt.label('l0'),
                       func.lead(AircraftBeacon.location_wkt).over(partition_by=AircraftBeacon.device_id, order_by=AircraftBeacon.timestamp).label('l1'),
                       AircraftBeacon.altitude.label('a0'),
                       func.lead(AircraftBeacon.altitude).over(partition_by=AircraftBeacon.device_id, order_by=AircraftBeacon.timestamp).label('a1')) \
        .filter(and_(func.date(AircraftBeacon.timestamp) == date,
                     AircraftBeacon.error_count == 0)) \
        .subquery()
        
    sq2 = session.query(sq.c.device_id,
                        (func.st_distancesphere(sq.c.l1, sq.c.l0) / (func.extract('epoch', sq.c.t1) - func.extract('epoch', sq.c.t0))).label('horizontal_speed'),
                        ((sq.c.a1 - sq.c.a0) / (func.extract('epoch', sq.c.t1) - func.extract('epoch', sq.c.t0))).label('vertical_speed')) \
        .filter(and_(sq.c.t0 != null(),
                     sq.c.t1 != null(),
                     sq.c.t0 < sq.c.t1)) \
        .subquery()
    
    sq3 = session.query(sq2.c.device_id,
                        case([(or_(func.abs(sq2.c.horizontal_speed) > 1000, func.abs(sq2.c.vertical_speed) > 100), 1)], else_=0).label('jump')) \
        .subquery()
        
    sq4 = session.query(sq3.c.device_id,
                        func.sum(sq3.c.jump).label('jumps')) \
        .group_by(sq3.c.device_id) \
        .subquery()
    
    upd = update(DeviceStats) \
        .where(and_(DeviceStats.date == date,
                    DeviceStats.device_id == sq4.c.device_id)) \
        .values({'ambiguous': sq4.c.jumps > 10,
                 'jumps': sq4.c.jumps})
        
    result = session.execute(upd)
    update_counter = result.rowcount
    session.commit()
    logger.warn("Updated {} DeviceStats jumps".format(update_counter))

    return "DeviceStats jumps for {}: {} updated".format(date, update_counter)

@app.task
def create_relation_stats(session=None, date=None):
    """Add/update relation stats."""

    if session is None:
        session = app.session

    if not date:
        logger.warn("A date is needed for calculating stats. Exiting")
        return None

    # First kill the stats for the selected date
    deleted_counter = session.query(RelationStats) \
        .filter(RelationStats.date == date) \
        .delete()

    # Calculate stats for selected day
    relation_stats = session.query(
            func.date(AircraftBeacon.timestamp),
            AircraftBeacon.device_id,
            AircraftBeacon.receiver_id,
            func.max(AircraftBeacon.quality),
            func.count(AircraftBeacon.id)
            ) \
        .filter(and_(func.date(AircraftBeacon.timestamp) == date,
                     AircraftBeacon.distance > 1000,
                     AircraftBeacon.error_count == 0,
                     AircraftBeacon.quality <= 40,
                     AircraftBeacon.ground_speed > 10)) \
        .group_by(func.date(AircraftBeacon.timestamp), AircraftBeacon.device_id, AircraftBeacon.receiver_id) \
        .subquery()

    # And insert them
    ins = insert(RelationStats).from_select(
        [RelationStats.date, RelationStats.device_id, RelationStats.receiver_id, RelationStats.quality, RelationStats.beacon_count],
        relation_stats)
    res = session.execute(ins)
    insert_counter = res.rowcount
    session.commit()
    logger.warn("RelationStats for {}: {} deleted, {} inserted".format(date, deleted_counter, insert_counter))

    return "RelationStats for {}: {} deleted, {} inserted".format(date, deleted_counter, insert_counter)

@app.task
def update_qualities(session=None, date=None):
    """Calculate relative qualities of receivers and devices."""
    
    if session is None:
        session = app.session
        
    if not date:
        logger.warn("A date is needed for update stats. Exiting")
        return None

    # Calculate avg quality of devices
    dev_sq = session.query(RelationStats.date,
                        RelationStats.device_id,
                        func.avg(RelationStats.quality).label('quality')) \
        .filter(RelationStats.date == date) \
        .group_by(RelationStats.date,
                  RelationStats.device_id) \
        .subquery()
        
    dev_upd = update(DeviceStats) \
        .where(and_(DeviceStats.date == dev_sq.c.date,
                    DeviceStats.device_id == dev_sq.c.device_id)) \
        .values({'quality': dev_sq.c.quality})
    
    dev_result = session.execute(dev_upd)
    dev_update_counter = dev_result.rowcount
    session.commit()
    logger.warn("Updated {} DeviceStats: quality".format(dev_update_counter)) 

    # Calculate avg quality of receivers
    rec_sq = session.query(RelationStats.date,
                        RelationStats.receiver_id,
                        func.avg(RelationStats.quality).label('quality')) \
        .filter(RelationStats.date == date) \
        .group_by(RelationStats.date,
                  RelationStats.receiver_id) \
        .subquery()
    
    rec_upd = update(ReceiverStats) \
        .where(and_(ReceiverStats.date == rec_sq.c.date,
                    ReceiverStats.receiver_id == rec_sq.c.receiver_id)) \
        .values({'quality': rec_sq.c.quality})
    
    rec_result = session.execute(rec_upd)
    rec_update_counter = rec_result.rowcount
    session.commit()
    logger.warn("Updated {} ReceiverStats: quality".format(rec_update_counter))   
    
    # Calculate quality_offset of devices
    dev_sq = session.query(RelationStats.date,
                        RelationStats.device_id,
                        (func.sum(RelationStats.beacon_count*(RelationStats.quality - ReceiverStats.quality))/(func.sum(RelationStats.beacon_count))).label('quality_offset')) \
        .filter(RelationStats.date == date) \
        .filter(and_(RelationStats.receiver_id == ReceiverStats.receiver_id,
                     RelationStats.date == ReceiverStats.date)) \
        .group_by(RelationStats.date,
                  RelationStats.device_id) \
        .subquery()
        
    dev_upd = update(DeviceStats) \
        .where(and_(DeviceStats.date == dev_sq.c.date,
                    DeviceStats.device_id == dev_sq.c.device_id)) \
        .values({'quality_offset': dev_sq.c.quality_offset})
    
    dev_result = session.execute(dev_upd)
    dev_update_counter = dev_result.rowcount
    session.commit()
    logger.warn("Updated {} DeviceStats: quality_offset".format(dev_update_counter)) 
    
    # Calculate quality_offset of receivers
    rec_sq = session.query(RelationStats.date,
                        RelationStats.receiver_id,
                        (func.sum(RelationStats.beacon_count*(RelationStats.quality - DeviceStats.quality))/(func.sum(RelationStats.beacon_count))).label('quality_offset')) \
        .filter(RelationStats.date == date) \
        .filter(and_(RelationStats.device_id == DeviceStats.device_id,
                     RelationStats.date == DeviceStats.date)) \
        .group_by(RelationStats.date,
                  RelationStats.receiver_id) \
        .subquery()
    
    rec_upd = update(ReceiverStats) \
        .where(and_(ReceiverStats.date == rec_sq.c.date,
                    ReceiverStats.receiver_id == rec_sq.c.receiver_id)) \
        .values({'quality_offset': rec_sq.c.quality_offset})
    
    rec_result = session.execute(rec_upd)
    rec_update_counter = rec_result.rowcount
    session.commit()
    logger.warn("Updated {} ReceiverStats: quality_offset".format(rec_update_counter))   
    
    return "Updated {} DeviceStats and {} ReceiverStats".format(dev_update_counter, rec_update_counter)


@app.task
def update_receivers_stats(session=None):
    """Update receivers with stats."""
    
    if session is None:
        session = app.session

    receiver_stats = session.query(
            distinct(ReceiverStats.receiver_id).label('receiver_id'),
            func.first_value(ReceiverStats.firstseen)
                .over(partition_by=ReceiverStats.receiver_id, order_by=case([(ReceiverStats.firstseen == null(), None)], else_=ReceiverStats.date).asc().nullslast())
                .label('firstseen'),
            func.first_value(ReceiverStats.lastseen)
                .over(partition_by=ReceiverStats.receiver_id, order_by=case([(ReceiverStats.lastseen == null(), None)], else_=ReceiverStats.date).desc().nullslast())
                .label('lastseen'),
            func.first_value(ReceiverStats.location_wkt)
                .over(partition_by=ReceiverStats.receiver_id, order_by=case([(ReceiverStats.location_wkt == null(), None)], else_=ReceiverStats.date).desc().nullslast())
                .label('location_wkt'),
            func.first_value(ReceiverStats.altitude)
                .over(partition_by=ReceiverStats.receiver_id, order_by=case([(ReceiverStats.altitude == null(), None)], else_=ReceiverStats.date).desc().nullslast())
                .label('altitude'),
            func.first_value(ReceiverStats.version)
                .over(partition_by=ReceiverStats.receiver_id, order_by=case([(ReceiverStats.version == null(), None)], else_=ReceiverStats.date).desc().nullslast())
                .label('version'),
            func.first_value(ReceiverStats.platform)
                .over(partition_by=ReceiverStats.receiver_id, order_by=case([(ReceiverStats.platform == null(), None)], else_=ReceiverStats.date).desc().nullslast())
                .label('platform')) \
        .order_by(ReceiverStats.receiver_id) \
        .subquery()
    
    upd = update(Receiver) \
        .where(and_(Receiver.id == receiver_stats.c.receiver_id)) \
        .values({'firstseen': receiver_stats.c.firstseen,
                 'lastseen': receiver_stats.c.lastseen,
                 'location': receiver_stats.c.location_wkt,
                 'altitude': receiver_stats.c.altitude,
                 'version': receiver_stats.c.version,
                 'platform': receiver_stats.c.platform})
    
    result = session.execute(upd)
    update_counter = result.rowcount
    session.commit()
    logger.warn("Updated {} Receivers".format(update_counter))   
    
    return "Updated {} Receivers".format(update_counter)

@app.task
def update_devices_stats(session=None):
    """Update devices with stats."""
    
    if session is None:
        session = app.session

    device_stats = session.query(
            distinct(DeviceStats.device_id).label('device_id'),
            func.first_value(DeviceStats.firstseen)
                .over(partition_by=DeviceStats.device_id, order_by=case([(DeviceStats.firstseen == null(), None)], else_=DeviceStats.date).asc().nullslast())
                .label('firstseen'),
            func.max(DeviceStats.lastseen)
                .over(partition_by=DeviceStats.device_id, order_by=case([(DeviceStats.lastseen == null(), None)], else_=DeviceStats.date).desc().nullslast())
                .label('lastseen'),
            func.first_value(DeviceStats.aircraft_type)
                .over(partition_by=DeviceStats.device_id, order_by=case([(DeviceStats.aircraft_type == null(), None)], else_=DeviceStats.date).desc().nullslast())
                .label('aircraft_type'),
            func.first_value(DeviceStats.stealth)
                .over(partition_by=DeviceStats.device_id, order_by=case([(DeviceStats.stealth == null(), None)], else_=DeviceStats.date).desc().nullslast())
                .label('stealth'),
            func.first_value(DeviceStats.software_version)
                .over(partition_by=DeviceStats.device_id, order_by=case([(DeviceStats.software_version == null(), None)], else_=DeviceStats.date).desc().nullslast())
                .label('software_version'),
            func.first_value(DeviceStats.hardware_version)
                .over(partition_by=DeviceStats.device_id, order_by=case([(DeviceStats.hardware_version == null(), None)], else_=DeviceStats.date).desc().nullslast())
                .label('hardware_version'),
            func.first_value(DeviceStats.real_address)
                .over(partition_by=DeviceStats.device_id, order_by=case([(DeviceStats.real_address == null(), None)], else_=DeviceStats.date).desc().nullslast())
                .label('real_address')) \
        .order_by(DeviceStats.device_id) \
        .subquery()
    
    upd = update(Device) \
        .where(and_(Device.id == device_stats.c.device_id)) \
        .values({'firstseen': device_stats.c.firstseen,
                 'lastseen': device_stats.c.lastseen,
                 'aircraft_type': device_stats.c.aircraft_type,
                 'stealth': device_stats.c.stealth,
                 'software_version': device_stats.c.software_version,
                 'hardware_version': device_stats.c.hardware_version,
                 'real_address': device_stats.c.real_address})
    
    result = session.execute(upd)
    update_counter = result.rowcount
    session.commit()
    logger.warn("Updated {} Devices".format(update_counter))   
    
    return "Updated {} Devices".format(update_counter)
