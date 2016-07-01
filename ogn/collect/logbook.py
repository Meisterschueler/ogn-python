from datetime import timedelta

from celery.utils.log import get_task_logger
from ogn.collect.celery import app

from sqlalchemy.sql import func, null
from sqlalchemy import and_, or_, insert, update, between, exists
from sqlalchemy.sql.expression import case, true, false, label

from ogn.model import AircraftBeacon, TakeoffLanding, Airport, Logbook

logger = get_task_logger(__name__)


def get_aircraft_beacon_start_id():
    # returns the last AircraftBeacon used for TakeoffLanding
    last_takeoff_landing_query = app.session.query(func.max(TakeoffLanding.id).label('max_id')) \
        .subquery()

    last_used_aircraft_beacon_query = app.session.query(AircraftBeacon.id) \
        .filter(TakeoffLanding.id == last_takeoff_landing_query.c.max_id) \
        .filter(and_(AircraftBeacon.timestamp == TakeoffLanding.timestamp,
                     AircraftBeacon.device_id == TakeoffLanding.device_id))

    last_used_aircraft_beacon_id = last_used_aircraft_beacon_query.first()
    if last_used_aircraft_beacon_id is None:
        min_aircraft_beacon_id = app.session.query(func.min(AircraftBeacon.id)).first()
        if min_aircraft_beacon_id is None:
            return 0
        else:
            start_id = min_aircraft_beacon_id[0]
    else:
        start_id = last_used_aircraft_beacon_id[0] + 1

    return start_id


@app.task
def compute_takeoff_and_landing():
    logger.info("Compute takeoffs and landings.")

    # takeoff / landing detection is based on 3 consecutive points
    takeoff_speed = 55  # takeoff detection: 1st point below, 2nd and 3rd above this limit
    landing_speed = 40  # landing detection: 1st point above, 2nd and 3rd below this limit
    duration = 100      # the points must not exceed this duration
    radius = 0.05       # the points must not exceed this radius (degree!) around the 2nd point

    # takeoff / landing has to be near an airport
    airport_radius = 0.025  # takeoff / landing must not exceed this radius (degree!) around the airport
    airport_delta = 100     # takeoff / landing must not exceed this altitude offset above/below the airport

    # AircraftBeacon start id and max id offset
    aircraft_beacon_start_id = get_aircraft_beacon_start_id()
    max_id_offset = 500000

    # 'wo' is the window order for the sql window function
    wo = and_(AircraftBeacon.device_id, AircraftBeacon.timestamp)

    # make a query with current, previous and next position
    sq = app.session.query(
        AircraftBeacon.id,
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
        func.lead(AircraftBeacon.altitude).over(order_by=wo).label('altitude_next'),
        AircraftBeacon.device_id,
        func.lag(AircraftBeacon.device_id).over(order_by=wo).label('device_id_prev'),
        func.lead(AircraftBeacon.device_id).over(order_by=wo).label('device_id_next')) \
        .filter(between(AircraftBeacon.id, aircraft_beacon_start_id, aircraft_beacon_start_id + max_id_offset)) \
        .subquery()

    # find possible takeoffs and landings
    sq2 = app.session.query(
        sq.c.id,
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
        sq2.c.is_takeoff,
        sq2.c.device_id,
        Airport.id) \
        .filter(and_(func.ST_DFullyWithin(sq2.c.location, Airport.location_wkt, airport_radius),
                     between(sq2.c.altitude, Airport.altitude - airport_delta, Airport.altitude + airport_delta))) \
        .filter(between(Airport.style, 2, 5)) \
        .order_by(sq2.c.id)

    # ... and save them
    ins = insert(TakeoffLanding).from_select((TakeoffLanding.timestamp,
                                              TakeoffLanding.track,
                                              TakeoffLanding.is_takeoff,
                                              TakeoffLanding.device_id,
                                              TakeoffLanding.airport_id),
                                             takeoff_landing_query)
    result = app.session.execute(ins)
    counter = result.rowcount
    app.session.commit()
    logger.debug("New takeoffs and landings: {}".format(counter))

    return counter


@app.task
def compute_logbook_entries():
    logger.info("Compute logbook.")

    or_args = [between(TakeoffLanding.timestamp, '2016-06-28 00:00:00', '2016-06-28 23:59:59')]
    or_args = []

    # 'wo' is the window order for the sql window function
    wo = and_(func.date(TakeoffLanding.timestamp),
              TakeoffLanding.device_id,
              TakeoffLanding.timestamp)

    # make a query with current, previous and next "takeoff_landing" event, so we can find complete flights
    sq = app.session.query(
            TakeoffLanding.device_id,
            func.lag(TakeoffLanding.device_id).over(order_by=wo).label('device_id_prev'),
            func.lead(TakeoffLanding.device_id).over(order_by=wo).label('device_id_next'),
            TakeoffLanding.timestamp,
            func.lag(TakeoffLanding.timestamp).over(order_by=wo).label('timestamp_prev'),
            func.lead(TakeoffLanding.timestamp).over(order_by=wo).label('timestamp_next'),
            TakeoffLanding.track,
            func.lag(TakeoffLanding.track).over(order_by=wo).label('track_prev'),
            func.lead(TakeoffLanding.track).over(order_by=wo).label('track_next'),
            TakeoffLanding.is_takeoff,
            func.lag(TakeoffLanding.is_takeoff).over(order_by=wo).label('is_takeoff_prev'),
            func.lead(TakeoffLanding.is_takeoff).over(order_by=wo).label('is_takeoff_next'),
            TakeoffLanding.airport_id,
            func.lag(TakeoffLanding.airport_id).over(order_by=wo).label('airport_id_prev'),
            func.lead(TakeoffLanding.airport_id).over(order_by=wo).label('airport_id_next')) \
        .filter(*or_args) \
        .subquery()

    # find complete flights (with takeoff and landing on the same day)
    complete_flight_query = app.session.query(
            sq.c.timestamp.label('reftime'),
            sq.c.device_id.label('device_id'),
            sq.c.timestamp.label('takeoff_timestamp'), sq.c.track.label('takeoff_track'), sq.c.airport_id.label('takeoff_airport_id'),
            sq.c.timestamp_next.label('landing_timestamp'), sq.c.track_next.label('landing_track'), sq.c.airport_id_next.label('landing_airport_id'),
            label('duration', sq.c.timestamp_next - sq.c.timestamp)) \
        .filter(and_(sq.c.is_takeoff == true(), sq.c.is_takeoff_next == false())) \
        .filter(sq.c.device_id == sq.c.device_id_next) \
        .filter(func.date(sq.c.timestamp_next) == func.date(sq.c.timestamp))

    # split complete flights (with takeoff and landing on different days) into one takeoff and one landing
    split_start_query = app.session.query(
            sq.c.timestamp.label('reftime'),
            sq.c.device_id.label('device_id'),
            sq.c.timestamp.label('takeoff_timestamp'), sq.c.track.label('takeoff_track'), sq.c.airport_id.label('takeoff_airport_id'),
            null().label('landing_timestamp'), null().label('landing_track'), null().label('landing_airport_id'),
            null().label('duration')) \
        .filter(and_(sq.c.is_takeoff == true(), sq.c.is_takeoff_next == false())) \
        .filter(sq.c.device_id == sq.c.device_id_next) \
        .filter(func.date(sq.c.timestamp_next) != func.date(sq.c.timestamp))

    split_landing_query = app.session.query(
            sq.c.timestamp_next.label('reftime'),
            sq.c.device_id.label('device_id'),
            null().label('takeoff_timestamp'), null().label('takeoff_track'), null().label('takeoff_airport_id'),
            sq.c.timestamp_next.label('landing_timestamp'), sq.c.track_next.label('landing_track'), sq.c.airport_id_next.label('landing_airport_id'),
            null().label('duration')) \
        .filter(and_(sq.c.is_takeoff == true(), sq.c.is_takeoff_next == false())) \
        .filter(sq.c.device_id == sq.c.device_id_next) \
        .filter(func.date(sq.c.timestamp_next) != func.date(sq.c.timestamp))

    # find landings without start
    only_landings_query = app.session.query(
            sq.c.timestamp.label('reftime'),
            sq.c.device_id.label('device_id'),
            null().label('takeoff_timestamp'), null().label('takeoff_track'), null().label('takeoff_airport_id'),
            sq.c.timestamp.label('landing_timestamp'), sq.c.track_next.label('landing_track'), sq.c.airport_id_next.label('landing_airport_id'),
            null().label('duration')) \
        .filter(sq.c.is_takeoff == false()) \
        .filter(or_(sq.c.device_id != sq.c.device_id_prev,
                    sq.c.is_takeoff_prev == false()))

    # find starts without landing
    only_starts_query = app.session.query(
            sq.c.timestamp.label('reftime'),
            sq.c.device_id.label('device_id'),
            sq.c.timestamp.label('takeoff_timestamp'), sq.c.track.label('takeoff_track'), sq.c.airport_id.label('takeoff_airport_id'),
            null().label('landing_timestamp'), null().label('landing_track'), null().label('landing_airport_id'),
            null().label('duration')) \
        .filter(sq.c.is_takeoff == true()) \
        .filter(or_(sq.c.device_id != sq.c.device_id_next,
                    sq.c.is_takeoff_next == true()))

    # update 'incomplete' logbook entries with 'complete flights'
    complete_flights = complete_flight_query.subquery()

    upd = update(Logbook) \
        .where(and_(Logbook.reftime == complete_flights.c.reftime,
                    Logbook.device_id == complete_flights.c.device_id,
                    or_(Logbook.takeoff_airport_id == complete_flights.c.takeoff_airport_id,
                        and_(Logbook.takeoff_airport_id == null(),
                             complete_flights.c.takeoff_airport_id == null())),
                    or_(Logbook.landing_airport_id == complete_flights.c.landing_airport_id,
                        and_(Logbook.landing_airport_id == null(),
                             complete_flights.c.landing_airport_id == null())))) \
        .values({"takeoff_timestamp": complete_flights.c.takeoff_timestamp,
                 "takeoff_track": complete_flights.c.takeoff_track,
                 "takeoff_airport_id": complete_flights.c.takeoff_airport_id,
                 "landing_timestamp": complete_flights.c.landing_timestamp,
                 "landing_track": complete_flights.c.landing_track,
                 "landing_airport_id": complete_flights.c.landing_airport_id,
                 "duration": complete_flights.c.duration})

    result = app.session.execute(upd)
    counter = result.rowcount
    app.session.commit()
    logger.debug("Updated logbook entries: {}".format(counter))

    # unite all computated flights ('incomplete' and 'complete')
    union_query = complete_flight_query.union(
            split_start_query,
            split_landing_query,
            only_landings_query,
            only_starts_query) \
        .subquery()

    # consider only if not already stored
    new_logbook_entries = app.session.query(union_query) \
        .filter(~exists().where(
            and_(Logbook.reftime == union_query.c.reftime,
                 Logbook.device_id == union_query.c.device_id,
                 or_(Logbook.takeoff_airport_id == union_query.c.takeoff_airport_id,
                     and_(Logbook.takeoff_airport_id == null(),
                          union_query.c.takeoff_airport_id == null())),
                 or_(Logbook.landing_airport_id == union_query.c.landing_airport_id,
                     and_(Logbook.landing_airport_id == null(),
                          union_query.c.landing_airport_id == null())))))

    # ... and save them
    ins = insert(Logbook).from_select((Logbook.reftime,
                                       Logbook.device_id,
                                       Logbook.takeoff_timestamp,
                                       Logbook.takeoff_track,
                                       Logbook.takeoff_airport_id,
                                       Logbook.landing_timestamp,
                                       Logbook.landing_track,
                                       Logbook.landing_airport_id,
                                       Logbook.duration),
                                      new_logbook_entries)

    result = app.session.execute(ins)
    counter = result.rowcount
    app.session.commit()
    logger.debug("New logbook entries: {}".format(counter))

    return counter
