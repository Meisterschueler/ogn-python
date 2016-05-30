from datetime import timedelta

from celery.utils.log import get_task_logger
from ogn.collect.celery import app

from sqlalchemy.sql import func
from sqlalchemy import and_, or_, insert
from sqlalchemy.sql.expression import case

from ogn.model import AircraftBeacon, TakeoffLanding

logger = get_task_logger(__name__)


@app.task
def compute_takeoff_and_landing():
    logger.info("Compute takeoffs and landings.")

    # takeoff / landing detection is based on 3 consecutive points
    takeoff_speed = 55  # takeoff detection: 1st point below, 2nd and 3rd above this limit
    landing_speed = 40  # landing detection: 1st point above, 2nd and 3rd below this limit
    duration = 100      # the points must not exceed this duration
    radius = 0.05       # the points must not exceed this radius (degree!) around the 2nd point

    # calculate the time where the computation starts
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
    end_computation = begin_computation + timedelta(days=30)

    logger.debug("Calculate takeoffs and landings between {} and {}"
                 .format(begin_computation, end_computation))

    # make a query with current, previous and next position
    sq = app.session.query(
        AircraftBeacon.address,
        func.lag(AircraftBeacon.address).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('address_prev'),
        func.lead(AircraftBeacon.address).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('address_next'),
        AircraftBeacon.timestamp,
        func.lag(AircraftBeacon.timestamp).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('timestamp_prev'),
        func.lead(AircraftBeacon.timestamp).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('timestamp_next'),
        AircraftBeacon.name,
        func.lag(AircraftBeacon.name).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('name_prev'),
        func.lead(AircraftBeacon.name).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('name_next'),
        AircraftBeacon.receiver_name,
        func.lag(AircraftBeacon.receiver_name).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('receiver_name_prev'),
        func.lead(AircraftBeacon.receiver_name).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('receiver_name_next'),
        AircraftBeacon.location_wkt,
        func.lag(AircraftBeacon.location_wkt).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('location_wkt_prev'),
        func.lead(AircraftBeacon.location_wkt).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('location_wkt_next'),
        AircraftBeacon.track,
        func.lag(AircraftBeacon.track).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('track_prev'),
        func.lead(AircraftBeacon.track).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('track_next'),
        AircraftBeacon.ground_speed,
        func.lag(AircraftBeacon.ground_speed).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('ground_speed_prev'),
        func.lead(AircraftBeacon.ground_speed).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('ground_speed_next'),
        AircraftBeacon.altitude,
        func.lag(AircraftBeacon.altitude).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('altitude_prev'),
        func.lead(AircraftBeacon.altitude).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('altitude_next')) \
        .filter(AircraftBeacon.timestamp >= begin_computation) \
        .filter(AircraftBeacon.timestamp <= end_computation) \
        .order_by(func.date(AircraftBeacon.timestamp), AircraftBeacon.address, AircraftBeacon.timestamp) \
        .subquery()

    # find takeoffs and landings
    takeoff_landing_query = app.session.query(
        sq.c.address,
        sq.c.name,
        sq.c.receiver_name,
        sq.c.timestamp,
        sq.c.location,
        sq.c.track,
        sq.c.ground_speed,
        sq.c.altitude,
        case([(sq.c.ground_speed > takeoff_speed, True),
              (sq.c.ground_speed < landing_speed, False)]).label('is_takeoff')) \
        .filter(sq.c.address_prev == sq.c.address == sq.c.address_next) \
        .filter(or_(and_(sq.c.ground_speed_prev < takeoff_speed,    # takeoff
                         sq.c.ground_speed > takeoff_speed,
                         sq.c.ground_speed_next > takeoff_speed),
                    and_(sq.c.ground_speed_prev > landing_speed,    # landing
                         sq.c.ground_speed < landing_speed,
                         sq.c.ground_speed_next < landing_speed))) \
        .filter(sq.c.timestamp_next - sq.c.timestamp_prev < timedelta(seconds=duration)) \
        .filter(and_(func.ST_DFullyWithin(sq.c.location, sq.c.location_wkt_prev, radius),
                     func.ST_DFullyWithin(sq.c.location, sq.c.location_wkt_next, radius))) \
        .order_by(func.date(sq.c.timestamp), sq.c.timestamp)

    # ... and save them
    ins = insert(TakeoffLanding).from_select((TakeoffLanding.address, TakeoffLanding.name, TakeoffLanding.receiver_name, TakeoffLanding.timestamp, TakeoffLanding.location_wkt, TakeoffLanding.track, TakeoffLanding.ground_speed, TakeoffLanding.altitude, TakeoffLanding.is_takeoff), takeoff_landing_query)
    result = app.session.execute(ins)
    counter = result.rowcount
    app.session.commit()
    logger.debug("New/recalculated takeoffs and landings: {}".format(counter))

    return counter
