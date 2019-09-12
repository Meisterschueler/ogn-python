from datetime import timedelta

from flask import current_app
from sqlalchemy import and_, or_, insert, between, exists
from sqlalchemy.sql import func, null
from sqlalchemy.sql.expression import case

from app.model import AircraftBeacon, TakeoffLanding, Airport


def update_entries(session, start, end, logger=None):
    """Compute takeoffs and landings."""

    if logger is None:
        logger = current_app.logger

    logger.info("Compute takeoffs and landings.")

    # considered time interval should not exceed a complete day
    if end - start > timedelta(days=1):
        abort_message = "TakeoffLanding: timeinterval start='{}' and end='{}' is too big.".format(start, end)
        logger.warn(abort_message)
        return abort_message

    # check if we have any airport
    airports_query = session.query(Airport).limit(1)
    if not airports_query.all():
        abort_message = "TakeoffLanding: Cannot calculate takeoff and landings without any airport! Please import airports first."
        logger.warn(abort_message)
        return abort_message

    # takeoff / landing detection is based on 3 consecutive points all below a certain altitude AGL
    takeoff_speed = 55  # takeoff detection: 1st point below, 2nd and 3rd above this limit
    landing_speed = 40  # landing detection: 1st point above, 2nd and 3rd below this limit
    min_takeoff_climb_rate = -5  # takeoff detection: glider should not sink too much
    max_landing_climb_rate = 5  # landing detection: glider should not climb too much
    duration = 100  # the points must not exceed this duration
    radius = 5000  # the points must not exceed this radius around the 2nd point
    max_agl = 200  # takeoff / landing must not exceed this altitude AGL

    # get beacons for selected time range, one per device_id and timestamp
    sq = (
        session.query(AircraftBeacon)
        .distinct(AircraftBeacon.device_id, AircraftBeacon.timestamp)
        .order_by(AircraftBeacon.device_id, AircraftBeacon.timestamp, AircraftBeacon.error_count)
        .filter(AircraftBeacon.agl < max_agl)
        .filter(between(AircraftBeacon.timestamp, start, end))
        .subquery()
    )

    # make a query with current, previous and next position
    sq2 = session.query(
        sq.c.device_id,
        func.lag(sq.c.device_id).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("device_id_prev"),
        func.lead(sq.c.device_id).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("device_id_next"),
        sq.c.timestamp,
        func.lag(sq.c.timestamp).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("timestamp_prev"),
        func.lead(sq.c.timestamp).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("timestamp_next"),
        sq.c.location,
        func.lag(sq.c.location).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("location_wkt_prev"),
        func.lead(sq.c.location).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("location_wkt_next"),
        sq.c.track,
        func.lag(sq.c.track).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("track_prev"),
        func.lead(sq.c.track).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("track_next"),
        sq.c.ground_speed,
        func.lag(sq.c.ground_speed).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("ground_speed_prev"),
        func.lead(sq.c.ground_speed).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("ground_speed_next"),
        sq.c.altitude,
        func.lag(sq.c.altitude).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("altitude_prev"),
        func.lead(sq.c.altitude).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("altitude_next"),
        sq.c.climb_rate,
        func.lag(sq.c.climb_rate).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("climb_rate_prev"),
        func.lead(sq.c.climb_rate).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label("climb_rate_next"),
    ).subquery()

    # consider only positions with predecessor and successor and limit distance and duration between points
    sq3 = (
        session.query(sq2)
        .filter(and_(sq2.c.device_id_prev != null(), sq2.c.device_id_next != null()))
        .filter(and_(func.ST_DistanceSphere(sq2.c.location, sq2.c.location_wkt_prev) < radius, func.ST_DistanceSphere(sq2.c.location, sq2.c.location_wkt_next) < radius))
        .filter(sq2.c.timestamp_next - sq2.c.timestamp_prev < timedelta(seconds=duration))
        .subquery()
    )

    # find possible takeoffs and landings
    sq4 = (
        session.query(
            sq3.c.timestamp,
            case(
                [
                    (sq3.c.ground_speed > takeoff_speed, sq3.c.location_wkt_prev),  # on takeoff we take the location from the previous fix because it is nearer to the airport
                    (sq3.c.ground_speed <= takeoff_speed, sq3.c.location),
                ]
            ).label("location"),
            case([(sq3.c.ground_speed > landing_speed, sq3.c.track), (sq3.c.ground_speed <= landing_speed, sq3.c.track_prev)]).label(
                "track"
            ),  # on landing we take the track from the previous fix because gliders tend to leave the runway quickly
            sq3.c.ground_speed,
            sq3.c.altitude,
            case([(sq3.c.ground_speed > takeoff_speed, True), (sq3.c.ground_speed < landing_speed, False)]).label("is_takeoff"),
            sq3.c.device_id,
        )
        .filter(
            or_(
                and_(sq3.c.ground_speed_prev < takeoff_speed, sq3.c.ground_speed > takeoff_speed, sq3.c.ground_speed_next > takeoff_speed, sq3.c.climb_rate > min_takeoff_climb_rate),  # takeoff
                and_(sq3.c.ground_speed_prev > landing_speed, sq3.c.ground_speed < landing_speed, sq3.c.ground_speed_next < landing_speed, sq3.c.climb_rate < max_landing_climb_rate),  # landing
            )
        )
        .subquery()
    )

    # consider them if the are near airports ...
    sq5 = (
        session.query(
            sq4.c.timestamp, sq4.c.track, sq4.c.is_takeoff, sq4.c.device_id, Airport.id.label("airport_id"), func.ST_DistanceSphere(sq4.c.location, Airport.location_wkt).label("airport_distance")
        )
        .filter(and_(func.ST_Within(sq4.c.location, Airport.border), between(Airport.style, 2, 5)))
        .subquery()
    )

    # ... and take the nearest airport
    sq6 = (
        session.query(sq5.c.timestamp, sq5.c.track, sq5.c.is_takeoff, sq5.c.device_id, sq5.c.airport_id)
        .distinct(sq5.c.timestamp, sq5.c.track, sq5.c.is_takeoff, sq5.c.device_id)
        .order_by(sq5.c.timestamp, sq5.c.track, sq5.c.is_takeoff, sq5.c.device_id, sq5.c.airport_distance)
        .subquery()
    )

    # consider them only if they are not already existing in db
    takeoff_landing_query = session.query(sq6).filter(
        ~exists().where(and_(TakeoffLanding.timestamp == sq6.c.timestamp, TakeoffLanding.device_id == sq6.c.device_id, TakeoffLanding.airport_id == sq6.c.airport_id))
    )

    # ... and save them
    ins = insert(TakeoffLanding).from_select((TakeoffLanding.timestamp, TakeoffLanding.track, TakeoffLanding.is_takeoff, TakeoffLanding.device_id, TakeoffLanding.airport_id), takeoff_landing_query)

    result = session.execute(ins)
    session.commit()
    insert_counter = result.rowcount

    finish_message = "TakeoffLandings: {} inserted".format(insert_counter)
    logger.info(finish_message)
    return finish_message
