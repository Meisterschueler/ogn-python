from sqlalchemy import Date
from sqlalchemy import and_, insert, update, exists, between
from sqlalchemy.sql import func, null
from flask import current_app

from app.model import AircraftBeacon, Receiver, ReceiverCoverage
from app.utils import date_to_timestamps


def update_entries(session, date, logger=None):
    """Create receiver coverage stats for Melissas ognrange."""

    if logger is None:
        logger = current_app.logger

    logger.info("Compute receiver coverages.")

    (start, end) = date_to_timestamps(date)

    # Filter aircraft beacons
    sq = (
        session.query(AircraftBeacon.location_mgrs_short, AircraftBeacon.receiver_name, AircraftBeacon.signal_quality, AircraftBeacon.altitude, AircraftBeacon.address)
        .filter(and_(between(AircraftBeacon.timestamp, start, end), AircraftBeacon.location_mgrs_short != null(), AircraftBeacon.receiver_name != null(), AircraftBeacon.address != null()))
        .subquery()
    )

    # ... and group them by reduced MGRS, receiver and date
    sq2 = (
        session.query(
            sq.c.location_mgrs_short,
            sq.c.receiver_name,
            func.cast(date, Date).label("date"),
            func.max(sq.c.signal_quality).label("max_signal_quality"),
            func.min(sq.c.altitude).label("min_altitude"),
            func.max(sq.c.altitude).label("max_altitude"),
            func.count(sq.c.altitude).label("aircraft_beacon_count"),
            func.count(func.distinct(sq.c.address)).label("device_count"),
        )
        .group_by(sq.c.location_mgrs_short, sq.c.receiver_name)
        .subquery()
    )

    # Replace receiver_name with receiver_id
    sq3 = (
        session.query(
            sq2.c.location_mgrs_short,
            Receiver.id.label("receiver_id"),
            sq2.c.date,
            sq2.c.max_signal_quality,
            sq2.c.min_altitude,
            sq2.c.max_altitude,
            sq2.c.aircraft_beacon_count,
            sq2.c.device_count,
        )
        .filter(sq2.c.receiver_name == Receiver.name)
        .subquery()
    )

    # if a receiver coverage entry exist --> update it
    upd = (
        update(ReceiverCoverage)
        .where(and_(ReceiverCoverage.location_mgrs_short == sq3.c.location_mgrs_short, ReceiverCoverage.receiver_id == sq3.c.receiver_id, ReceiverCoverage.date == date))
        .values(
            {
                "max_signal_quality": sq3.c.max_signal_quality,
                "min_altitude": sq3.c.min_altitude,
                "max_altitude": sq3.c.max_altitude,
                "aircraft_beacon_count": sq3.c.aircraft_beacon_count,
                "device_count": sq3.c.device_count,
            }
        )
    )

    result = session.execute(upd)
    update_counter = result.rowcount
    session.commit()
    logger.debug("Updated receiver coverage entries: {}".format(update_counter))

    # if a receiver coverage entry doesnt exist --> insert it
    new_coverage_entries = session.query(sq3).filter(
        ~exists().where(and_(ReceiverCoverage.location_mgrs_short == sq3.c.location_mgrs_short, ReceiverCoverage.receiver_id == sq3.c.receiver_id, ReceiverCoverage.date == date))
    )

    ins = insert(ReceiverCoverage).from_select(
        (
            ReceiverCoverage.location_mgrs_short,
            ReceiverCoverage.receiver_id,
            ReceiverCoverage.date,
            ReceiverCoverage.max_signal_quality,
            ReceiverCoverage.min_altitude,
            ReceiverCoverage.max_altitude,
            ReceiverCoverage.aircraft_beacon_count,
            ReceiverCoverage.device_count,
        ),
        new_coverage_entries,
    )

    result = session.execute(ins)
    insert_counter = result.rowcount
    session.commit()

    finish_message = "ReceiverCoverage: {} inserted, {} updated".format(insert_counter, update_counter)
    logger.debug(finish_message)
    return finish_message
