from sqlalchemy import and_, or_, insert, update, exists, between
from sqlalchemy.sql import func, null
from sqlalchemy.sql.expression import case, true, false
from flask import current_app

from app.model import Airport, SenderPosition, Sender, TakeoffLanding, Logbook
from app.utils import date_to_timestamps

from datetime import datetime, timedelta

from app import db


# takeoff / landing detection is based on 3 consecutive points
MIN_TAKEOFF_SPEED = 55          # takeoff detection: 1st point below, 2nd and 3rd above this limit
MAX_LANDING_SPEED = 40          # landing detection: 1st point above, 2nd and 3rd below this limit
MIN_TAKEOFF_CLIMB_RATE = -5     # takeoff detection: glider should not sink too much
MAX_LANDING_SINK_RATE = 5       # landing detection: glider should not climb too much
MAX_EVENT_DURATION = 100        # the points must not exceed this duration
MAX_EVENT_RADIUS = 5000         # the points must not exceed this radius around the 2nd point
MAX_EVENT_AGL = 200             # takeoff / landing must not exceed this altitude AGL


def update_takeoff_landings(start, end):
    """Compute takeoffs and landings."""

    current_app.logger.info("Compute takeoffs and landings.")

    # considered time interval should not exceed a complete day
    if end - start > timedelta(days=1):
        abort_message = "TakeoffLanding: timeinterval start='{}' and end='{}' is too big.".format(start, end)
        current_app.logger.warn(abort_message)
        return abort_message

    # check if we have any airport
    airports_query = db.session.query(Airport).limit(1)
    if not airports_query.all():
        abort_message = "TakeoffLanding: Cannot calculate takeoff and landings without any airport! Please import airports first."
        current_app.logger.warn(abort_message)
        return abort_message

    # delete existing elements
    db.session.query(TakeoffLanding) \
        .filter(between(TakeoffLanding.timestamp, start, end))\
        .delete(synchronize_session='fetch')
    db.session.commit()

    # get beacons for selected time range (+ buffer for duration), one per name and timestamp
    sq = (
        db.session.query(SenderPosition.name, SenderPosition.timestamp, SenderPosition.location, SenderPosition.track, db.func.coalesce(SenderPosition.ground_speed, 0.0).label("ground_speed"), SenderPosition.altitude, db.func.coalesce(SenderPosition.climb_rate, 0.0).label("climb_rate"))
        .distinct(SenderPosition.name, SenderPosition.timestamp)
        .order_by(SenderPosition.name, SenderPosition.timestamp, SenderPosition.error_count)
        .filter(SenderPosition.agl <= MAX_EVENT_AGL)
        .filter(between(SenderPosition.reference_timestamp, start - timedelta(seconds=MAX_EVENT_DURATION), end + timedelta(seconds=MAX_EVENT_DURATION)))
        .subquery()
    )
    
    # make a query with current, previous and next position
    sq2 = db.session.query(
        sq.c.name,
        func.lag(sq.c.name).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("name_prev"),
        func.lead(sq.c.name).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("name_next"),
        sq.c.timestamp,
        func.lag(sq.c.timestamp).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("timestamp_prev"),
        func.lead(sq.c.timestamp).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("timestamp_next"),
        sq.c.location,
        func.lag(sq.c.location).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("location_wkt_prev"),
        func.lead(sq.c.location).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("location_wkt_next"),
        sq.c.track,
        func.lag(sq.c.track).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("track_prev"),
        func.lead(sq.c.track).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("track_next"),
        sq.c.ground_speed,
        func.lag(sq.c.ground_speed).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("ground_speed_prev"),
        func.lead(sq.c.ground_speed).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("ground_speed_next"),
        sq.c.altitude,
        func.lag(sq.c.altitude).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("altitude_prev"),
        func.lead(sq.c.altitude).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("altitude_next"),
        sq.c.climb_rate,
        func.lag(sq.c.climb_rate).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("climb_rate_prev"),
        func.lead(sq.c.climb_rate).over(partition_by=sq.c.name, order_by=sq.c.timestamp).label("climb_rate_next"),
    ).subquery()

    # consider only positions between start and end and with predecessor and successor and limit distance and duration between points
    sq3 = (
        db.session.query(sq2)
        .filter(and_(sq2.c.name_prev != null(), sq2.c.name_next != null()))
        .filter(and_(func.ST_DistanceSphere(sq2.c.location, sq2.c.location_wkt_prev) < MAX_EVENT_RADIUS, func.ST_DistanceSphere(sq2.c.location, sq2.c.location_wkt_next) < MAX_EVENT_RADIUS))
        .filter(sq2.c.timestamp_next - sq2.c.timestamp_prev < timedelta(seconds=MAX_EVENT_DURATION))
        .filter(between(sq2.c.timestamp, start, end))
        .subquery()
    )

    # find possible takeoffs and landings
    sq4 = (
        db.session.query(
            sq3.c.timestamp,
            case(
                [
                    (sq3.c.ground_speed > MIN_TAKEOFF_SPEED, sq3.c.location_wkt_prev),  # on takeoff we take the location from the previous fix because it is nearer to the airport
                    (sq3.c.ground_speed <= MIN_TAKEOFF_SPEED, sq3.c.location),
                ]
            ).label("location"),
            case([(sq3.c.ground_speed > MAX_LANDING_SPEED, sq3.c.track), (sq3.c.ground_speed <= MAX_LANDING_SPEED, sq3.c.track_prev)]).label(
                "track"
            ),  # on landing we take the track from the previous fix because gliders tend to leave the runway quickly
            sq3.c.ground_speed,
            sq3.c.altitude,
            case([(sq3.c.ground_speed > MIN_TAKEOFF_SPEED, True), (sq3.c.ground_speed < MAX_LANDING_SPEED, False)]).label("is_takeoff"),
            sq3.c.name,
        )
        .filter(
            or_(
                and_(sq3.c.ground_speed_prev < MIN_TAKEOFF_SPEED, sq3.c.ground_speed > MIN_TAKEOFF_SPEED, sq3.c.ground_speed_next > MIN_TAKEOFF_SPEED, sq3.c.climb_rate > MIN_TAKEOFF_CLIMB_RATE),  # takeoff
                and_(sq3.c.ground_speed_prev > MAX_LANDING_SPEED, sq3.c.ground_speed < MAX_LANDING_SPEED, sq3.c.ground_speed_next < MAX_LANDING_SPEED, sq3.c.climb_rate < MAX_LANDING_SINK_RATE),  # landing
            )
        )
        .subquery()
    )

    # get the device id instead of the name and consider them if the are near airports ...
    sq5 = (
        db.session.query(
            sq4.c.timestamp, sq4.c.track, sq4.c.is_takeoff, Sender.id.label("device_id"), Airport.id.label("airport_id"), func.ST_DistanceSphere(sq4.c.location, Airport.location_wkt).label("airport_distance")
        )
        .filter(and_(func.ST_Within(sq4.c.location, Airport.border),
                     between(Airport.style, 2, 5)))
        .filter(sq4.c.name == Sender.name)
        .subquery()
    )

    # ... and take the nearest airport
    takeoff_landing_query = (
        db.session.query(sq5.c.timestamp, sq5.c.track, sq5.c.is_takeoff, sq5.c.device_id, sq5.c.airport_id)
        .distinct(sq5.c.timestamp, sq5.c.track, sq5.c.is_takeoff, sq5.c.device_id)
        .order_by(sq5.c.timestamp, sq5.c.track, sq5.c.is_takeoff, sq5.c.device_id, sq5.c.airport_distance)
        .subquery()
    )

    # ... and save them
    ins = insert(TakeoffLanding).from_select((TakeoffLanding.timestamp, TakeoffLanding.track, TakeoffLanding.is_takeoff, TakeoffLanding.sender_id, TakeoffLanding.airport_id), takeoff_landing_query)

    result = db.session.execute(ins)
    db.session.commit()
    insert_counter = result.rowcount

    finish_message = "TakeoffLandings: {} inserted".format(insert_counter)
    current_app.logger.info(finish_message)
    return finish_message


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        result = update_takeoff_landings(start=datetime(2020, 11, 9, 10, 0, 0), end=datetime(2020, 11, 9, 10, 10, 0))
        print(result)


def update_logbook(offset_days):
    """Add/update logbook entries."""

    current_app.logger.info("Compute logbook.")

    # limit time range to given date and set window partition and window order
    (start, end) = date_to_timestamps(datetime.utcnow()-timedelta(days=offset_days))
    pa = TakeoffLanding.sender_id
    wo = and_(TakeoffLanding.sender_id, TakeoffLanding.timestamp, TakeoffLanding.airport_id)

    # delete existing elements
    db.session.query(Logbook)\
        .filter(between(Logbook.reference, start, end))\
        .delete(synchronize_session='fetch')
    db.session.commit()

    # make a query with current and next "takeoff_landing" event, so we can find complete flights
    sq = (
        db.session.query(
            TakeoffLanding.sender_id,
            func.lead(TakeoffLanding.sender_id).over(partition_by=pa, order_by=wo).label("sender_id_next"),
            TakeoffLanding.timestamp,
            func.lead(TakeoffLanding.timestamp).over(partition_by=pa, order_by=wo).label("timestamp_next"),
            TakeoffLanding.track,
            func.lead(TakeoffLanding.track).over(partition_by=pa, order_by=wo).label("track_next"),
            TakeoffLanding.is_takeoff,
            func.lead(TakeoffLanding.is_takeoff).over(partition_by=pa, order_by=wo).label("is_takeoff_next"),
            TakeoffLanding.airport_id,
            func.lead(TakeoffLanding.airport_id).over(partition_by=pa, order_by=wo).label("airport_id_next")
        )
        .filter(between(TakeoffLanding.timestamp, start, end))
        .subquery()
    )

    # find complete flights
    complete_flight_query = (
        db.session.query(
            sq.c.sender_id.label("sender_id"),
            sq.c.timestamp.label("takeoff_timestamp"),
            sq.c.track.label("takeoff_track"),
            sq.c.airport_id.label("takeoff_airport_id"),
            sq.c.timestamp_next.label("landing_timestamp"),
            sq.c.track_next.label("landing_track"),
            sq.c.airport_id_next.label("landing_airport_id"),
        )
        .filter(sq.c.is_takeoff == true())
        .filter(sq.c.is_takeoff_next == false())
    )

    # find landings without start
    only_landings_query = (
        db.session.query(
            sq.c.sender_id_next.label("sender_id"),
            null().label("takeoff_timestamp"),
            null().label("takeoff_track"),
            null().label("takeoff_airport_id"),
            sq.c.timestamp_next.label("landing_timestamp"),
            sq.c.track_next.label("landing_track"),
            sq.c.airport_id_next.label("landing_airport_id"),
        )
        .filter(or_(sq.c.is_takeoff == false(), sq.c.is_takeoff == null()))
        .filter(sq.c.is_takeoff_next == false())
    )

    # find starts without landing
    only_starts_query = (
        db.session.query(
            sq.c.sender_id.label("sender_id"),
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
            Logbook.sender_id,
            Logbook.takeoff_timestamp,
            Logbook.takeoff_track,
            Logbook.takeoff_airport_id,
            Logbook.landing_timestamp,
            Logbook.landing_track,
            Logbook.landing_airport_id,
        ),
        logbook_entries,
    )

    result = db.session.execute(ins)
    insert_counter = result.rowcount
    db.session.commit()

    finish_message = "Logbook: {} inserted".format(insert_counter)
    return finish_message


def update_max_altitudes(date, logger=None):
    """Add max altitudes in logbook when flight is complete (takeoff and landing)."""

    if logger is None:
        logger = current_app.logger

    current_app.logger.info("Update logbook max altitude.")

    (start, end) = date_to_timestamps(date)

    logbook_entries = (
        db.query(Logbook.id)
        .filter(and_(Logbook.takeoff_timestamp != null(), Logbook.landing_timestamp != null(), Logbook.max_altitude == null()))
        .filter(between(Logbook.reference, start, end))
        .subquery()
    )

    max_altitudes = (
        db.query(Logbook.id, func.max(SenderPosition.altitude).label("max_altitude"))
        .filter(Logbook.id == logbook_entries.c.id)
        .filter(and_(SenderPosition.address == Logbook.address, SenderPosition.timestamp >= Logbook.takeoff_timestamp, SenderPosition.timestamp <= Logbook.landing_timestamp))
        .group_by(Logbook.id)
        .subquery()
    )

    update_logbook = db.query(Logbook).filter(Logbook.id == max_altitudes.c.id).update({Logbook.max_altitude: max_altitudes.c.max_altitude}, synchronize_session="fetch")

    db.session.commit()

    finish_message = "Logbook (altitude): {} entries updated.".format(update_logbook)
    return finish_message
