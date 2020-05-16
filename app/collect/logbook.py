from sqlalchemy import and_, or_, insert, update, exists, between
from sqlalchemy.sql import func, null
from sqlalchemy.sql.expression import true, false
from flask import current_app

from app.model import TakeoffLanding, Logbook, AircraftBeacon
from app.utils import date_to_timestamps


def update_entries(session, date, logger=None):
    """Add/update logbook entries."""

    if logger is None:
        logger = current_app.logger

    logger.info("Compute logbook.")

    # limit time range to given date and set window partition and window order
    (start, end) = date_to_timestamps(date)
    pa = TakeoffLanding.address
    wo = and_(TakeoffLanding.address, TakeoffLanding.airport_id, TakeoffLanding.timestamp)

    # delete existing elements
    session.query(Logbook)\
        .filter(between(Logbook.reftime, start, end))\
        .delete(synchronize_session='fetch')
    session.commit()

    # make a query with current, previous and next "takeoff_landing" event, so we can find complete flights
    sq = (
        session.query(
            TakeoffLanding.address,
            func.lag(TakeoffLanding.address).over(partition_by=pa, order_by=wo).label("address_prev"),
            func.lead(TakeoffLanding.address).over(partition_by=pa, order_by=wo).label("address_next"),
            TakeoffLanding.timestamp,
            func.lag(TakeoffLanding.timestamp).over(partition_by=pa, order_by=wo).label("timestamp_prev"),
            func.lead(TakeoffLanding.timestamp).over(partition_by=pa, order_by=wo).label("timestamp_next"),
            TakeoffLanding.track,
            func.lag(TakeoffLanding.track).over(partition_by=pa, order_by=wo).label("track_prev"),
            func.lead(TakeoffLanding.track).over(partition_by=pa, order_by=wo).label("track_next"),
            TakeoffLanding.is_takeoff,
            func.lag(TakeoffLanding.is_takeoff).over(partition_by=pa, order_by=wo).label("is_takeoff_prev"),
            func.lead(TakeoffLanding.is_takeoff).over(partition_by=pa, order_by=wo).label("is_takeoff_next"),
            TakeoffLanding.airport_id,
            func.lag(TakeoffLanding.airport_id).over(partition_by=pa, order_by=wo).label("airport_id_prev"),
            func.lead(TakeoffLanding.airport_id).over(partition_by=pa, order_by=wo).label("airport_id_next"),
        )
        .filter(between(TakeoffLanding.timestamp, start, end))
        .subquery()
    )

    # find complete flights
    complete_flight_query = session.query(
        sq.c.timestamp.label("reftime"),
        sq.c.address.label("address"),
        sq.c.timestamp.label("takeoff_timestamp"),
        sq.c.track.label("takeoff_track"),
        sq.c.airport_id.label("takeoff_airport_id"),
        sq.c.timestamp_next.label("landing_timestamp"),
        sq.c.track_next.label("landing_track"),
        sq.c.airport_id_next.label("landing_airport_id"),
    ).filter(and_(sq.c.is_takeoff == true(), sq.c.is_takeoff_next == false()))

    # find landings without start
    only_landings_query = (
        session.query(
            sq.c.timestamp.label("reftime"),
            sq.c.address.label("address"),
            null().label("takeoff_timestamp"),
            null().label("takeoff_track"),
            null().label("takeoff_airport_id"),
            sq.c.timestamp.label("landing_timestamp"),
            sq.c.track.label("landing_track"),
            sq.c.airport_id.label("landing_airport_id"),
        )
        .filter(sq.c.is_takeoff == false())
        .filter(or_(sq.c.is_takeoff_prev == false(), sq.c.is_takeoff_prev == null()))
    )

    # find starts without landing
    only_starts_query = (
        session.query(
            sq.c.timestamp.label("reftime"),
            sq.c.address.label("address"),
            sq.c.timestamp.label("takeoff_timestamp"),
            sq.c.track.label("takeoff_track"),
            sq.c.airport_id.label("takeoff_airport_id"),
            null().label("landing_timestamp"),
            null().label("landing_track"),
            null().label("landing_airport_id"),
        )
        .filter(sq.c.is_takeoff == true())
        .filter(or_(sq.c.is_takeoff_next == true(), sq.c.is_takeoff_next == null()))
    )

    # unite all computated flights
    logbook_entries = complete_flight_query.union(only_landings_query, only_starts_query).subquery()

    # ... insert them into logbook
    ins = insert(Logbook).from_select(
        (
            Logbook.reftime,
            Logbook.address,
            Logbook.takeoff_timestamp,
            Logbook.takeoff_track,
            Logbook.takeoff_airport_id,
            Logbook.landing_timestamp,
            Logbook.landing_track,
            Logbook.landing_airport_id,
        ),
        logbook_entries,
    )

    result = session.execute(ins)
    insert_counter = result.rowcount
    session.commit()

    finish_message = "Logbook: {} inserted".format(insert_counter)
    logger.debug(finish_message)
    return finish_message


def update_max_altitudes(session, date, logger=None):
    """Add max altitudes in logbook when flight is complete (takeoff and landing)."""

    if logger is None:
        logger = current_app.logger

    logger.info("Update logbook max altitude.")

    if session is None:
        session = current_app.session

    (start, end) = date_to_timestamps(date)

    logbook_entries = (
        session.query(Logbook.id)
        .filter(and_(Logbook.takeoff_timestamp != null(), Logbook.landing_timestamp != null(), Logbook.max_altitude == null()))
        .filter(between(Logbook.reftime, start, end))
        .subquery()
    )

    max_altitudes = (
        session.query(Logbook.id, func.max(AircraftBeacon.altitude).label("max_altitude"))
        .filter(Logbook.id == logbook_entries.c.id)
        .filter(and_(AircraftBeacon.address == Logbook.address, AircraftBeacon.timestamp >= Logbook.takeoff_timestamp, AircraftBeacon.timestamp <= Logbook.landing_timestamp))
        .group_by(Logbook.id)
        .subquery()
    )

    update_logbook = session.query(Logbook).filter(Logbook.id == max_altitudes.c.id).update({Logbook.max_altitude: max_altitudes.c.max_altitude}, synchronize_session="fetch")

    session.commit()

    finish_message = "Logbook (altitude): {} entries updated.".format(update_logbook)
    logger.info(finish_message)
    return finish_message
