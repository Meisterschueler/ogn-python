from datetime import datetime, timedelta

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

    takeoff_speed = 30
    landing_speed = 30

    # calculate the time where the computation starts
    last_takeoff_landing_query = app.session.query(func.max(TakeoffLanding.timestamp))
    last_takeoff_landing = last_takeoff_landing_query.one()[0]
    if last_takeoff_landing is None:
        # if the table is empty
        last_takeoff_landing = datetime(2015, 1, 1, 0, 0, 0)
    else:
        # we get the beacons async. to be safe we delete takeoffs/landings from last 5 minutes and recalculate from then
        # alternative: takeoff/landing has a primary key (timestamp,address)
        last_takeoff_landing = last_takeoff_landing - timedelta(minutes=5)
        app.session.query(TakeoffLanding) \
            .filter(TakeoffLanding.timestamp > last_takeoff_landing) \
            .delete()

    # make a query with current, previous and next position, so we can detect takeoffs and landings
    sq = app.session.query(
        AircraftBeacon.address,
        func.lag(AircraftBeacon.address).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('address_prev'),
        func.lead(AircraftBeacon.address).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('address_next'),
        AircraftBeacon.timestamp,
        func.lag(AircraftBeacon.timestamp).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('timestamp_prev'),
        func.lead(AircraftBeacon.timestamp).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('timestamp_next'),
        AircraftBeacon.latitude,
        func.lag(AircraftBeacon.latitude).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('latitude_prev'),
        func.lead(AircraftBeacon.latitude).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('latitude_next'),
        AircraftBeacon.longitude,
        func.lag(AircraftBeacon.longitude).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('longitude_prev'),
        func.lead(AircraftBeacon.longitude).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('longitude_next'),
        AircraftBeacon.ground_speed,
        AircraftBeacon.track,
        func.lag(AircraftBeacon.track).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('track_prev'),
        func.lead(AircraftBeacon.track).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('track_next'),
        AircraftBeacon.ground_speed,
        func.lag(AircraftBeacon.ground_speed).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('ground_speed_prev'),
        func.lead(AircraftBeacon.ground_speed).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('ground_speed_next'),
        AircraftBeacon.altitude,
        func.lag(AircraftBeacon.altitude).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('altitude_prev'),
        func.lead(AircraftBeacon.altitude).over(order_by=and_(AircraftBeacon.address, AircraftBeacon.timestamp)).label('altitude_next')) \
        .filter(AircraftBeacon.timestamp > last_takeoff_landing) \
        .order_by(func.date(AircraftBeacon.timestamp), AircraftBeacon.address, AircraftBeacon.timestamp) \
        .subquery()

    # find takeoffs and landings (look at the trigger_speed)
    takeoff_landing_query = app.session.query(
        sq.c.address,
        sq.c.timestamp,
        sq.c.latitude,
        sq.c.longitude,
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
        .order_by(func.date(sq.c.timestamp), sq.c.timestamp)

    # ... and save them
    ins = insert(TakeoffLanding).from_select((TakeoffLanding.address, TakeoffLanding.timestamp, TakeoffLanding.latitude, TakeoffLanding.longitude, TakeoffLanding.track, TakeoffLanding.ground_speed, TakeoffLanding.altitude, TakeoffLanding.is_takeoff), takeoff_landing_query)
    result = app.session.execute(ins)
    counter = result.rowcount
    app.session.commit()
    logger.debug("New/recalculated takeoffs and landings: {}".format(counter))

    return counter
