from celery.utils.log import get_task_logger

from sqlalchemy import String
from sqlalchemy import and_, insert, update, exists, between
from sqlalchemy.sql import func, null
from sqlalchemy.sql.expression import literal_column

from ogn.collect.celery import app
from ogn.model import AircraftBeacon, ReceiverCoverage
from ogn.utils import date_to_timestamps

logger = get_task_logger(__name__)


@app.task
def create_receiver_coverage(session=None, date=None):
    """Create receiver coverages."""

    logger.info("Compute receiver coverages.")

    if session is None:
        session = app.session

    if not date:
        logger.warn("A date is needed for calculating stats. Exiting")
        return None
    else:
        (start, end) = date_to_timestamps(date)

    # Filter aircraft beacons and shrink precision of MGRS from 1m to 1km resolution: 30UXC 00061 18429 -> 30UXC 00 18
    sq = session.query((func.left(AircraftBeacon.location_mgrs, 5, type_=String) + func.substring(AircraftBeacon.location_mgrs, 6, 2, type_=String) + func.substring(AircraftBeacon.location_mgrs, 11, 2, type_=String)).label('reduced_mgrs'),
                       AircraftBeacon.receiver_id,
                       AircraftBeacon.signal_quality,
                       AircraftBeacon.altitude,
                       AircraftBeacon.device_id) \
        .filter(and_(between(AircraftBeacon.timestamp, start, end),
                     AircraftBeacon.location_mgrs != null(),
                     AircraftBeacon.receiver_id != null(),
                     AircraftBeacon.device_id != null())) \
        .subquery()

    # ... and group them by reduced MGRS, receiver and date
    query = session.query(sq.c.reduced_mgrs,
                          sq.c.receiver_id,
                          literal_column("'{}'".format(date.strftime('%Y-%m-%d'))).label('date'),
                          func.max(sq.c.signal_quality).label('max_signal_quality'),
                          func.min(sq.c.altitude).label('min_altitude'),
                          func.max(sq.c.altitude).label('max_altitude'),
                          func.count(sq.c.altitude).label('aircraft_beacon_count'),
                          func.count(func.distinct(sq.c.device_id)).label('device_count')) \
        .group_by(sq.c.reduced_mgrs,
                  sq.c.receiver_id) \
        .subquery()

    # if a receiver coverage entry exist --> update it
    upd = update(ReceiverCoverage) \
        .where(and_(ReceiverCoverage.location_mgrs == query.c.reduced_mgrs,
                    ReceiverCoverage.receiver_id == query.c.receiver_id,
                    ReceiverCoverage.date == query.c.date)) \
        .values({"max_signal_quality": query.c.max_signal_quality,
                 "min_altitude": query.c.min_altitude,
                 "max_altitude": query.c.max_altitude,
                 "aircraft_beacon_count": query.c.aircraft_beacon_count,
                 "device_count": query.c.device_count})

    result = session.execute(upd)
    update_counter = result.rowcount
    session.commit()
    logger.debug("Updated receiver coverage entries: {}".format(update_counter))

    # if a receiver coverage entry doesnt exist --> insert it
    new_coverage_entries = session.query(query) \
        .filter(~exists().where(
            and_(ReceiverCoverage.location_mgrs == query.c.reduced_mgrs,
                 ReceiverCoverage.receiver_id == query.c.receiver_id,
                 ReceiverCoverage.date == query.c.date)))

    ins = insert(ReceiverCoverage).from_select((
            ReceiverCoverage.location_mgrs,
            ReceiverCoverage.receiver_id,
            ReceiverCoverage.date,
            ReceiverCoverage.max_signal_quality,
            ReceiverCoverage.min_altitude,
            ReceiverCoverage.max_altitude,
            ReceiverCoverage.aircraft_beacon_count,
            ReceiverCoverage.device_count),
        new_coverage_entries)

    result = session.execute(ins)
    insert_counter = result.rowcount
    session.commit()
    logger.debug("New receiver coverage entries: {}".format(insert_counter))

    return "Receiver coverage entries: {} inserted, {} updated".format(insert_counter, update_counter)
