from datetime import timedelta

from celery.utils.log import get_task_logger
from ogn.collect.celery import app

from sqlalchemy.sql import func
from sqlalchemy import and_, or_, insert, between
from sqlalchemy.sql.expression import case

from ogn.model import AircraftBeacon, TakeoffLanding, Airport

logger = get_task_logger(__name__)


@app.task
def compute_takeoff_and_landing():
    logger.info("Compute takeoffs and landings.")

    # takeoff / landing detection is based on 3 consecutive points
    takeoff_speed = 55  # takeoff detection: 1st point below, 2nd and 3rd above this limit
    landing_speed = 40  # landing detection: 1st point above, 2nd and 3rd below this limit
    duration = 100      # the points must not exceed this duration
    radius = 0.05       # the points must not exceed this radius (degree!) around the 2nd point

    # takeoff / landing has to be near an airport
    airport_radius = 0.05   # takeoff / landing must not exceed this radius (degree!) around the airport
    airport_delta = 200     # takeoff / landing must not exceed this altitude offset above/below the airport

    # calculate the start (and stop) timestamp for the computatio
    last_takeoff_landing_query = app.session.query(func.max(TakeoffLanding.timestamp))
    begin_computation = last_takeoff_landing_query.one()[0]
    if begin_computation is None:
        # if the table is empty
        last_takeoff_landing_query = app.session.query(func.min(AircraftBeacon.timestamp))
        begin_computation = last_takeoff_landing_query.one()[0]
        if begin_computation is None:
            return 0
    else:
        # we get the beacons async. to be safe we delete takeoffs/landings from last 24 hours and recalculate from then
        begin_computation = begin_computation - timedelta(hours=24)
        app.session.query(TakeoffLanding) \
            .filter(TakeoffLanding.timestamp >= begin_computation) \
            .delete()
    end_computation = begin_computation + timedelta(days=5)

    logger.debug("Calculate takeoffs and landings between {} and {}"
                 .format(begin_computation, end_computation))

    # make a query with current, previous and next position
    sq = app.session.query(
        AircraftBeacon.timestamp,
        func.lag(AircraftBeacon.timestamp).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('timestamp_prev'),
        func.lead(AircraftBeacon.timestamp).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('timestamp_next'),
        AircraftBeacon.location_wkt,
        func.lag(AircraftBeacon.location_wkt).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('location_wkt_prev'),
        func.lead(AircraftBeacon.location_wkt).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('location_wkt_next'),
        AircraftBeacon.track,
        func.lag(AircraftBeacon.track).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('track_prev'),
        func.lead(AircraftBeacon.track).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('track_next'),
        AircraftBeacon.ground_speed,
        func.lag(AircraftBeacon.ground_speed).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('ground_speed_prev'),
        func.lead(AircraftBeacon.ground_speed).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('ground_speed_next'),
        AircraftBeacon.altitude,
        func.lag(AircraftBeacon.altitude).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('altitude_prev'),
        func.lead(AircraftBeacon.altitude).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('altitude_next'),
        AircraftBeacon.device_id,
        func.lag(AircraftBeacon.device_id).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('device_id_prev'),
        func.lead(AircraftBeacon.device_id).over(order_by=and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)).label('device_id_next')) \
        .filter(AircraftBeacon.timestamp >= begin_computation) \
        .filter(AircraftBeacon.timestamp <= end_computation) \
        .subquery()

    # find possible takeoffs and landings
    sq2 = app.session.query(
        sq.c.timestamp,
        case([(sq.c.ground_speed > takeoff_speed, sq.c.location_wkt_prev),  # on takeoff we take the location from the previous fix because it is nearer to the airport
              (sq.c.ground_speed < landing_speed, sq.c.location)]).label('location'),
        case([(sq.c.ground_speed > takeoff_speed, sq.c.track),
              (sq.c.ground_speed < landing_speed, sq.c.track_prev)]).label('track'),    # on landing we take the track from the previous fix because gliders tend to leave the runway quickly
        sq.c.ground_speed,
        sq.c.altitude,
        case([(sq.c.ground_speed > takeoff_speed, True),
              (sq.c.ground_speed < landing_speed, False)]).label('is_takeoff'),
        sq.c.device_id) \
        .filter(sq.c.device_id_prev == sq.c.device_id == sq.c.device_id_next) \
        .filter(or_(and_(sq.c.ground_speed_prev < takeoff_speed,    # takeoff
                         sq.c.ground_speed > takeoff_speed,
                         sq.c.ground_speed_next > takeoff_speed),
                    and_(sq.c.ground_speed_prev > landing_speed,    # landing
                         sq.c.ground_speed < landing_speed,
                         sq.c.ground_speed_next < landing_speed))) \
        .filter(sq.c.timestamp_next - sq.c.timestamp_prev < timedelta(seconds=duration)) \
        .filter(and_(func.ST_DFullyWithin(sq.c.location, sq.c.location_wkt_prev, radius),
                     func.ST_DFullyWithin(sq.c.location, sq.c.location_wkt_next, radius))) \
        .subquery()

    # consider them if they are near a airport
    takeoff_landing_query = app.session.query(
        sq2.c.timestamp,
        sq2.c.track,
        sq2.c.ground_speed,
        sq2.c.altitude,
        sq2.c.is_takeoff,
        sq2.c.device_id,
        Airport.id) \
        .filter(and_(func.ST_DFullyWithin(sq2.c.location, Airport.location_wkt, airport_radius),
                     between(sq2.c.altitude, Airport.altitude-airport_delta, Airport.altitude+airport_delta))) \
        .filter(between(Airport.style, 2, 5))

    # ... and save them
    ins = insert(TakeoffLanding).from_select((TakeoffLanding.timestamp,
                                              TakeoffLanding.track,
                                              TakeoffLanding.ground_speed,
                                              TakeoffLanding.altitude,
                                              TakeoffLanding.is_takeoff,
                                              TakeoffLanding.device_id,
                                              TakeoffLanding.airport_id),
                                             takeoff_landing_query)
    result = app.session.execute(ins)
    counter = result.rowcount
    app.session.commit()
    logger.debug("New/recalculated takeoffs and landings: {}".format(counter))

    return counter
