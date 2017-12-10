from datetime import timedelta

from celery.utils.log import get_task_logger

from sqlalchemy import and_, or_, insert, between, exists
from sqlalchemy.sql import func, null
from sqlalchemy.sql.expression import case
from sqlalchemy.orm import aliased

from ogn.collect.celery import app
from ogn.model import AircraftBeacon, TakeoffLanding, Airport

logger = get_task_logger(__name__)


@app.task
def update_takeoff_landing(session=None):
    logger.info("Compute takeoffs and landings.")

    if session is None:
        session = app.session

    # check if we have any airport
    airports_query = session.query(Airport)
    if not airports_query.all():
        logger.warn("Cannot calculate takeoff and landings without any airport! Please import airports first.")
        return

    # takeoff / landing detection is based on 3 consecutive points
    takeoff_speed = 55  # takeoff detection: 1st point below, 2nd and 3rd above this limit
    landing_speed = 40  # landing detection: 1st point above, 2nd and 3rd below this limit
    duration = 100      # the points must not exceed this duration
    radius = 0.05       # the points must not exceed this radius (degree!) around the 2nd point

    # takeoff / landing has to be near an airport
    airport_radius = 0.025  # takeoff / landing must not exceed this radius (degree!) around the airport
    airport_delta = 100     # takeoff / landing must not exceed this altitude offset above/below the airport

    # 'wo' is the window order for the sql window function
    wo = and_(AircraftBeacon.device_id,
              AircraftBeacon.timestamp,
              AircraftBeacon.receiver_id)

    # make a query with current, previous and next position
    beacon_selection = session.query(AircraftBeacon.id) \
        .filter(AircraftBeacon.status == null()) \
        .order_by(AircraftBeacon.timestamp) \
        .limit(1000000) \
        .subquery()

    sq = session.query(
        AircraftBeacon.id,
        func.lag(AircraftBeacon.id).over(order_by=wo).label('id_prev'),
        func.lead(AircraftBeacon.id).over(order_by=wo).label('id_next'),
        AircraftBeacon.device_id,
        func.lag(AircraftBeacon.device_id).over(order_by=wo).label('device_id_prev'),
        func.lead(AircraftBeacon.device_id).over(order_by=wo).label('device_id_next')) \
        .filter(AircraftBeacon.id == beacon_selection.c.id) \
        .subquery()

    # consider only positions with the same device id
    sq2 = session.query(sq) \
       .filter(sq.c.device_id_prev == sq.c.device_id == sq.c.device_id_next) \
       .subquery()

    # Get timestamps, locations, tracks, ground_speeds and altitudes
    prev_ab = aliased(AircraftBeacon, name="prev_ab")
    lead_ab = aliased(AircraftBeacon, name="lead_ab")

    sq3 = session.query(
        sq2.c.id,
        sq2.c.id_prev,
        sq2.c.id_next,
        sq2.c.device_id,
        sq2.c.device_id_prev,
        sq2.c.device_id_next,
        AircraftBeacon.timestamp,
        prev_ab.timestamp.label('timestamp_prev'),
        lead_ab.timestamp.label('timestamp_next'),
        AircraftBeacon.location_wkt,
        prev_ab.location_wkt.label('location_wkt_prev'),
        lead_ab.location_wkt.label('location_wkt_next'),
        AircraftBeacon.track,
        prev_ab.track.label('track_prev'),
        lead_ab.track.label('track_next'),
        AircraftBeacon.ground_speed,
        prev_ab.ground_speed.label('ground_speed_prev'),
        lead_ab.ground_speed.label('ground_speed_next'),
        AircraftBeacon.altitude,
        prev_ab.altitude.label('altitude_prev'),
        lead_ab.altitude.label('altitude_next')) \
        .filter(and_(sq2.c.id == AircraftBeacon.id, sq2.c.id_prev == prev_ab.id, sq2.c.id_next == lead_ab.id)) \
        .subquery()

    # find possible takeoffs and landings
    sq4 = session.query(
        sq3.c.id,
        sq3.c.timestamp,
        case([(sq3.c.ground_speed > takeoff_speed, sq3.c.location_wkt_prev),  # on takeoff we take the location from the previous fix because it is nearer to the airport
              (sq3.c.ground_speed < landing_speed, sq3.c.location)]).label('location'),
        case([(sq3.c.ground_speed > takeoff_speed, sq3.c.track),
              (sq3.c.ground_speed < landing_speed, sq3.c.track_prev)]).label('track'),    # on landing we take the track from the previous fix because gliders tend to leave the runway quickly
        sq3.c.ground_speed,
        sq3.c.altitude,
        case([(sq3.c.ground_speed > takeoff_speed, True),
              (sq3.c.ground_speed < landing_speed, False)]).label('is_takeoff'),
        sq3.c.device_id) \
        .filter(sq3.c.timestamp_next - sq3.c.timestamp_prev < timedelta(seconds=duration)) \
        .filter(and_(func.ST_DFullyWithin(sq3.c.location, sq3.c.location_wkt_prev, radius),
                     func.ST_DFullyWithin(sq3.c.location, sq3.c.location_wkt_next, radius))) \
        .filter(or_(and_(sq3.c.ground_speed_prev < takeoff_speed,    # takeoff
                         sq3.c.ground_speed > takeoff_speed,
                         sq3.c.ground_speed_next > takeoff_speed),
                    and_(sq3.c.ground_speed_prev > landing_speed,    # landing
                         sq3.c.ground_speed < landing_speed,
                         sq3.c.ground_speed_next < landing_speed))) \
        .subquery()

    # consider them if they are near a airport
    sq5 = session.query(
        sq4.c.timestamp,
        sq4.c.track,
        sq4.c.is_takeoff,
        sq4.c.device_id,
        Airport.id.label('airport_id')) \
        .filter(and_(func.ST_DFullyWithin(sq4.c.location, Airport.location_wkt, airport_radius),
                     between(sq4.c.altitude, Airport.altitude - airport_delta, Airport.altitude + airport_delta))) \
        .filter(between(Airport.style, 2, 5)) \
        .subquery()

    # consider them only if they are not already existing in db
    takeoff_landing_query = session.query(sq5) \
        .filter(~exists().where(
            and_(TakeoffLanding.timestamp == sq5.c.timestamp,
                 TakeoffLanding.device_id == sq5.c.device_id,
                 TakeoffLanding.airport_id == sq5.c.airport_id)))

    # ... and save them
    ins = insert(TakeoffLanding).from_select((TakeoffLanding.timestamp,
                                              TakeoffLanding.track,
                                              TakeoffLanding.is_takeoff,
                                              TakeoffLanding.device_id,
                                              TakeoffLanding.airport_id),
                                             takeoff_landing_query)
    result = session.execute(ins)
    counter = result.rowcount

    # mark the computated AircraftBeacons as 'used'
    update_aircraft_beacons = session.query(AircraftBeacon) \
        .filter(AircraftBeacon.id == sq2.c.id) \
        .update({AircraftBeacon.status: 0},
                synchronize_session='fetch')

    session.commit()
    logger.debug("Inserted {} TakeoffLandings, updated {} AircraftBeacons".format(counter, update_aircraft_beacons))

    return counter
