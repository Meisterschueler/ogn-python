from datetime import datetime, timedelta

from celery.utils.log import get_task_logger

from sqlalchemy import and_, or_, insert, update, between, exists
from sqlalchemy.sql import func, null
from sqlalchemy.sql.expression import case

from ogn.collect.celery import app
from ogn.model import AircraftBeacon, TakeoffLanding, Airport

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

    # takeoff / landing detection is based on 3 consecutive points
    takeoff_speed = 55  # takeoff detection: 1st point below, 2nd and 3rd above this limit
    landing_speed = 40  # landing detection: 1st point above, 2nd and 3rd below this limit
    duration = 100      # the points must not exceed this duration
    radius = 5000       # the points must not exceed this radius around the 2nd point

    # takeoff / landing has to be near an airport
    airport_radius = 2500   # takeoff / landing must not exceed this radius around the airport
    airport_delta = 100     # takeoff / landing must not exceed this altitude offset above/below the airport

    # 'wo' is the window order for the sql window function
    wo = and_(func.date(AircraftBeacon.timestamp),
              AircraftBeacon.device_id,
              AircraftBeacon.timestamp)

    # get beacons for selected day and filter out duplicates (e.g. from multiple receivers)
    sq = session.query(AircraftBeacon.id,
                       func.row_number().over(partition_by=(func.date(AircraftBeacon.timestamp),
                                                            AircraftBeacon.device_id,
                                                            AircraftBeacon.timestamp),
                                              order_by=AircraftBeacon.error_count).label('row')) \
        .filter(func.date(AircraftBeacon.timestamp) == date) \
        .subquery()
    
    sq2 = session.query(sq.c.id) \
        .filter(sq.c.row == 1) \
        .subquery()
        
    # make a query with current, previous and next position
    sq3 = session.query(
        AircraftBeacon.device_id,
        func.lag(AircraftBeacon.device_id).over(order_by=wo).label('device_id_prev'),
        func.lead(AircraftBeacon.device_id).over(order_by=wo).label('device_id_next'),
        AircraftBeacon.timestamp,
        func.lag(AircraftBeacon.timestamp).over(order_by=wo).label('timestamp_prev'),
        func.lead(AircraftBeacon.timestamp).over(order_by=wo).label('timestamp_next'),
        AircraftBeacon.location_wkt,
        func.lag(AircraftBeacon.location_wkt).over(order_by=wo).label('location_wkt_prev'),
        func.lead(AircraftBeacon.location_wkt).over(order_by=wo).label('location_wkt_next'),
        AircraftBeacon.track,
        func.lag(AircraftBeacon.track).over(order_by=wo).label('track_prev'),
        func.lead(AircraftBeacon.track).over(order_by=wo).label('track_next'),
        AircraftBeacon.ground_speed,
        func.lag(AircraftBeacon.ground_speed).over(order_by=wo).label('ground_speed_prev'),
        func.lead(AircraftBeacon.ground_speed).over(order_by=wo).label('ground_speed_next'),
        AircraftBeacon.altitude,
        func.lag(AircraftBeacon.altitude).over(order_by=wo).label('altitude_prev'),
        func.lead(AircraftBeacon.altitude).over(order_by=wo).label('altitude_next')) \
        .filter(AircraftBeacon.id == sq2.c.id) \
        .subquery()
        
    # consider only positions with the same device id
    sq4 = session.query(sq3) \
       .filter(sq3.c.device_id_prev == sq3.c.device_id == sq3.c.device_id_next) \
       .subquery()
       
    # find possible takeoffs and landings
    sq5 = session.query(
        sq4.c.timestamp,
        case([(sq4.c.ground_speed > takeoff_speed, sq4.c.location_wkt_prev),  # on takeoff we take the location from the previous fix because it is nearer to the airport
              (sq4.c.ground_speed < landing_speed, sq4.c.location)]).label('location'),
        case([(sq4.c.ground_speed > takeoff_speed, sq4.c.track),
              (sq4.c.ground_speed < landing_speed, sq4.c.track_prev)]).label('track'),    # on landing we take the track from the previous fix because gliders tend to leave the runway quickly
        sq4.c.ground_speed,
        sq4.c.altitude,
        case([(sq4.c.ground_speed > takeoff_speed, True),
              (sq4.c.ground_speed < landing_speed, False)]).label('is_takeoff'),
        sq4.c.device_id) \
        .filter(sq4.c.timestamp_next - sq4.c.timestamp_prev < timedelta(seconds=duration)) \
        .filter(and_(func.ST_DistanceSphere(sq4.c.location, sq4.c.location_wkt_prev) < radius,
                     func.ST_DistanceSphere(sq4.c.location, sq4.c.location_wkt_next) < radius)) \
        .filter(or_(and_(sq4.c.ground_speed_prev < takeoff_speed,    # takeoff
                         sq4.c.ground_speed > takeoff_speed,
                         sq4.c.ground_speed_next > takeoff_speed),
                    and_(sq4.c.ground_speed_prev > landing_speed,    # landing
                         sq4.c.ground_speed < landing_speed,
                         sq4.c.ground_speed_next < landing_speed))) \
        .subquery()
    
    # consider them if they are near a airport
    sq6 = session.query(
        sq5.c.timestamp,
        sq5.c.track,
        sq5.c.is_takeoff,
        sq5.c.device_id,
        Airport.id.label('airport_id')) \
        .filter(and_(func.ST_DistanceSphere(sq5.c.location, Airport.location_wkt) < airport_radius,
                     between(sq5.c.altitude, Airport.altitude - airport_delta, Airport.altitude + airport_delta))) \
        .filter(between(Airport.style, 2, 5)) \
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
