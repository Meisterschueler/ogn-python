from datetime import timedelta

from celery.utils.log import get_task_logger

from sqlalchemy import and_, or_, insert, between, exists
from sqlalchemy.sql import func, null
from sqlalchemy.sql.expression import case

from ogn_python.collect.celery import app
from ogn_python.model import AircraftBeacon, TakeoffLanding, Airport
from ogn_python.utils import date_to_timestamps

logger = get_task_logger(__name__)


@app.task
def update_takeoff_landings(session=None, date=None):
    """Compute takeoffs and landings."""

    logger.info("Compute takeoffs and landings.")

    if session is None:
        session = app.session

    # check if we have any airport
    airports_query = session.query(Airport).limit(1)
    if not airports_query.all():
        logger.warn("Cannot calculate takeoff and landings without any airport! Please import airports first.")
        return

    # takeoff / landing detection is based on 3 consecutive points all below a certain altitude AGL
    takeoff_speed = 55  # takeoff detection: 1st point below, 2nd and 3rd above this limit
    landing_speed = 40  # landing detection: 1st point above, 2nd and 3rd below this limit
    duration = 100      # the points must not exceed this duration
    radius = 5000       # the points must not exceed this radius around the 2nd point
    max_agl = 100       # takeoff / landing must not exceed this altitude AGL

    # limit time range to given date
    if date is not None:
        (start, end) = date_to_timestamps(date)
        filters = [between(AircraftBeacon.timestamp, start, end)]
    else:
        filters = []

    # get beacons for selected day, one per device_id and timestamp
    sq = session.query(AircraftBeacon) \
        .distinct(AircraftBeacon.device_id, AircraftBeacon.timestamp) \
        .order_by(AircraftBeacon.device_id, AircraftBeacon.timestamp, AircraftBeacon.error_count) \
        .filter(AircraftBeacon.agl < max_agl) \
        .filter(*filters) \
        .subquery()

    # make a query with current, previous and next position
    sq2 = session.query(
        sq.c.device_id,
        func.lag(sq.c.device_id).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('device_id_prev'),
        func.lead(sq.c.device_id).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('device_id_next'),
        sq.c.timestamp,
        func.lag(sq.c.timestamp).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('timestamp_prev'),
        func.lead(sq.c.timestamp).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('timestamp_next'),
        sq.c.location,
        func.lag(sq.c.location).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('location_wkt_prev'),
        func.lead(sq.c.location).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('location_wkt_next'),
        sq.c.track,
        func.lag(sq.c.track).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('track_prev'),
        func.lead(sq.c.track).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('track_next'),
        sq.c.ground_speed,
        func.lag(sq.c.ground_speed).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('ground_speed_prev'),
        func.lead(sq.c.ground_speed).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('ground_speed_next'),
        sq.c.altitude,
        func.lag(sq.c.altitude).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('altitude_prev'),
        func.lead(sq.c.altitude).over(partition_by=sq.c.device_id, order_by=sq.c.timestamp).label('altitude_next')) \
        .subquery()

    # consider only positions with predecessor and successor and limit distance and duration between points
    sq3 = session.query(sq2) \
        .filter(and_(sq2.c.device_id_prev != null(),
                     sq2.c.device_id_next != null())) \
        .filter(and_(func.ST_DistanceSphere(sq2.c.location, sq2.c.location_wkt_prev) < radius,
                     func.ST_DistanceSphere(sq2.c.location, sq2.c.location_wkt_next) < radius)) \
        .filter(sq2.c.timestamp_next - sq2.c.timestamp_prev < timedelta(seconds=duration)) \
        .subquery()

    # find possible takeoffs and landings
    sq4 = session.query(
        sq3.c.timestamp,
        case([(sq3.c.ground_speed > takeoff_speed, sq3.c.location_wkt_prev),                # on takeoff we take the location from the previous fix because it is nearer to the airport
              (sq3.c.ground_speed <= takeoff_speed, sq3.c.location)]).label('location'),
        case([(sq3.c.ground_speed > landing_speed, sq3.c.track),
              (sq3.c.ground_speed <= landing_speed, sq3.c.track_prev)]).label('track'),     # on landing we take the track from the previous fix because gliders tend to leave the runway quickly
        sq3.c.ground_speed,
        sq3.c.altitude,
        case([(sq3.c.ground_speed > takeoff_speed, True),
              (sq3.c.ground_speed < landing_speed, False)]).label('is_takeoff'),
        sq3.c.device_id) \
        .filter(or_(and_(sq3.c.ground_speed_prev < takeoff_speed,    # takeoff
                         sq3.c.ground_speed > takeoff_speed,
                         sq3.c.ground_speed_next > takeoff_speed),
                    and_(sq3.c.ground_speed_prev > landing_speed,    # landing
                         sq3.c.ground_speed < landing_speed,
                         sq3.c.ground_speed_next < landing_speed))) \
        .subquery()

    # consider them if the are near airports ...
    sq5 = session.query(
        sq4.c.timestamp,
        sq4.c.track,
        sq4.c.is_takeoff,
        sq4.c.device_id,
        Airport.id.label('airport_id'),
        func.ST_DistanceSphere(sq4.c.location, Airport.location_wkt).label('airport_distance')) \
        .filter(and_(func.ST_Within(sq4.c.location, Airport.border),
                     between(Airport.style, 2, 5))) \
        .subquery()

    # ... and take the nearest airport
    sq6 = session.query(sq5.c.timestamp, sq5.c.track, sq5.c.is_takeoff, sq5.c.device_id, sq5.c.airport_id) \
        .distinct(sq5.c.timestamp, sq5.c.track, sq5.c.is_takeoff, sq5.c.device_id, sq5.c.airport_id) \
        .order_by(sq5.c.timestamp, sq5.c.track, sq5.c.is_takeoff, sq5.c.device_id, sq5.c.airport_id, sq5.c.airport_distance) \
        .subquery()

    # consider them only if they are not already existing in db
    takeoff_landing_query = session.query(sq6) \
        .filter(~exists().where(
            and_(TakeoffLanding.timestamp == sq6.c.timestamp,
                 TakeoffLanding.device_id == sq6.c.device_id,
                 TakeoffLanding.airport_id == sq6.c.airport_id)))

    # ... and save them
    ins = insert(TakeoffLanding).from_select((TakeoffLanding.timestamp,
                                              TakeoffLanding.track,
                                              TakeoffLanding.is_takeoff,
                                              TakeoffLanding.device_id,
                                              TakeoffLanding.airport_id),
                                             takeoff_landing_query)

    result = session.execute(ins)
    session.commit()
    insert_counter = result.rowcount
    logger.warn("Inserted {} TakeoffLandings".format(insert_counter))

    return "Inserted {} TakeoffLandings".format(insert_counter)
