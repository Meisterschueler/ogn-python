from datetime import datetime, timedelta

from sqlalchemy.sql import func, null
from sqlalchemy import and_, or_, insert, between
from sqlalchemy.sql.expression import case, true, false, label

from ogn.db import session
from ogn.model import Flarm, Position, TakeoffLanding


def compute_takeoff_and_landing():
    takeoff_speed = 30
    landing_speed = 30

    # get last takeoff_landing time as starting point for the following search
    last_takeoff_landing_query = session.query(func.max(TakeoffLanding.timestamp))
    last_takeoff_landing = last_takeoff_landing_query.one()[0]
    if last_takeoff_landing is None:
        last_takeoff_landing = datetime(2015, 1, 1, 0, 0, 0)

    # make a query with current, previous and next position, so we can detect takeoffs and landings
    sq = session.query(Position.address,
                       func.lag(Position.address).over(order_by=and_(Position.address, Position.timestamp)).label('address_prev'),
                       func.lead(Position.address).over(order_by=and_(Position.address, Position.timestamp)).label('address_next'),
                       Position.timestamp,
                       func.lag(Position.timestamp).over(order_by=and_(Position.address, Position.timestamp)).label('timestamp_prev'),
                       func.lead(Position.timestamp).over(order_by=and_(Position.address, Position.timestamp)).label('timestamp_next'),
                       Position.latitude,
                       func.lag(Position.latitude).over(order_by=and_(Position.address, Position.timestamp)).label('latitude_prev'),
                       func.lead(Position.latitude).over(order_by=and_(Position.address, Position.timestamp)).label('latitude_next'),
                       Position.longitude,
                       func.lag(Position.longitude).over(order_by=and_(Position.address, Position.timestamp)).label('longitude_prev'),
                       func.lead(Position.longitude).over(order_by=and_(Position.address, Position.timestamp)).label('longitude_next'),
                       Position.ground_speed,
                       Position.track,
                       func.lag(Position.track).over(order_by=and_(Position.address, Position.timestamp)).label('track_prev'),
                       func.lead(Position.track).over(order_by=and_(Position.address, Position.timestamp)).label('track_next'),
                       Position.ground_speed,
                       func.lag(Position.ground_speed).over(order_by=and_(Position.address, Position.timestamp)).label('ground_speed_prev'),
                       func.lead(Position.ground_speed).over(order_by=and_(Position.address, Position.timestamp)).label('ground_speed_next'),
                       Position.altitude,
                       func.lag(Position.altitude).over(order_by=and_(Position.address, Position.timestamp)).label('altitude_prev'),
                       func.lead(Position.altitude).over(order_by=and_(Position.address, Position.timestamp)).label('altitude_next')) \
        .filter(Position.timestamp > last_takeoff_landing) \
        .order_by(func.date(Position.timestamp), Position.address, Position.timestamp) \
        .subquery()

    # find takeoffs and landings (look at the trigger_speed)
    takeoff_landing_query = session.query(sq.c.address, sq.c.timestamp, sq.c.latitude, sq.c.longitude, sq.c.track, sq.c.ground_speed, sq.c.altitude, case([(sq.c.ground_speed>takeoff_speed, True), (sq.c.ground_speed<landing_speed, False)]).label('is_takeoff')) \
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
    session.execute(ins)
    session.commit()


def get_logbook(airport_name, latitude, longitude, altitude):
    latmin = latitude - 0.15
    latmax = latitude + 0.15
    lonmin = longitude - 0.15
    lonmax = longitude + 0.15
    max_altitude = altitude + 200

    # make a query with current, previous and next "takeoff_landing" event, so we can find complete flights
    sq = session.query(TakeoffLanding.address,
                       func.lag(TakeoffLanding.address).over(order_by=and_(func.date(TakeoffLanding.timestamp), TakeoffLanding.address, TakeoffLanding.timestamp)).label('address_prev'),
                       func.lead(TakeoffLanding.address).over(order_by=and_(func.date(TakeoffLanding.timestamp), TakeoffLanding.address, TakeoffLanding.timestamp)).label('address_next'),
                       TakeoffLanding.timestamp,
                       func.lag(TakeoffLanding.timestamp).over(order_by=and_(func.date(TakeoffLanding.timestamp), TakeoffLanding.address, TakeoffLanding.timestamp)).label('timestamp_prev'),
                       func.lead(TakeoffLanding.timestamp).over(order_by=and_(func.date(TakeoffLanding.timestamp), TakeoffLanding.address, TakeoffLanding.timestamp)).label('timestamp_next'),
                       TakeoffLanding.track,
                       func.lag(TakeoffLanding.track).over(order_by=and_(func.date(TakeoffLanding.timestamp), TakeoffLanding.address, TakeoffLanding.timestamp)).label('track_prev'),
                       func.lead(TakeoffLanding.track).over(order_by=and_(func.date(TakeoffLanding.timestamp), TakeoffLanding.address, TakeoffLanding.timestamp)).label('track_next'),
                       TakeoffLanding.is_takeoff,
                       func.lag(TakeoffLanding.is_takeoff).over(order_by=and_(func.date(TakeoffLanding.timestamp), TakeoffLanding.address, TakeoffLanding.timestamp)).label('is_takeoff_prev'),
                       func.lead(TakeoffLanding.is_takeoff).over(order_by=and_(func.date(TakeoffLanding.timestamp), TakeoffLanding.address, TakeoffLanding.timestamp)).label('is_takeoff_next')) \
        .filter(and_(between(TakeoffLanding.latitude, latmin, latmax), between(TakeoffLanding.longitude, lonmin, lonmax))) \
        .filter(TakeoffLanding.altitude < max_altitude) \
        .subquery()

    # find complete flights (with takeoff and landing) with duration < 1 day
    complete_flight_query = session.query(sq.c.timestamp.label('reftime'), sq.c.address.label('address'), sq.c.timestamp.label('takeoff'), sq.c.track.label('takeoff_track'), sq.c.timestamp_next.label('landing'), sq.c.track_next.label('landing_track'), label('duration', sq.c.timestamp_next - sq.c.timestamp)) \
        .filter(and_(sq.c.is_takeoff == true(), sq.c.is_takeoff_next == false())) \
        .filter(sq.c.address == sq.c.address_next) \
        .filter(sq.c.timestamp_next - sq.c.timestamp < timedelta(days=1))

    # split complete flights (with takeoff and landing) with duration > 1 day into one takeoff and one landing
    split_start_query = session.query(sq.c.timestamp.label('reftime'), sq.c.address.label('address'), sq.c.timestamp.label('takeoff'), sq.c.track.label('takeoff_track'), null().label('landing'), null().label('landing_track'),  null().label('duration')) \
        .filter(and_(sq.c.is_takeoff == true(), sq.c.is_takeoff_next == false())) \
        .filter(sq.c.address == sq.c.address_next) \
        .filter(sq.c.timestamp_next - sq.c.timestamp >= timedelta(days=1))

    split_landing_query = session.query(sq.c.timestamp_next.label('reftime'), sq.c.address.label('address'), null().label('takeoff'), null().label('takeoff_track'), sq.c.timestamp_next.label('landing'), sq.c.track_next.label('landing_track'), null().label('duration')) \
        .filter(and_(sq.c.is_takeoff == true(), sq.c.is_takeoff_next == false())) \
        .filter(sq.c.address == sq.c.address_next) \
        .filter(sq.c.timestamp_next - sq.c.timestamp >= timedelta(days=1))

    # find landings without start
    only_landings_query = session.query(sq.c.timestamp.label('reftime'), sq.c.address.label('address'), null().label('takeoff'), null().label('takeoff_track'), sq.c.timestamp.label('landing'), sq.c.track_next.label('landing_track'), null().label('duration')) \
        .filter(sq.c.is_takeoff == false()) \
        .filter(or_(sq.c.address != sq.c.address_prev,
                    sq.c.is_takeoff_prev == false()))

    # find starts without landing
    only_starts_query = session.query(sq.c.timestamp.label('reftime'), sq.c.address.label('address'), sq.c.timestamp.label('takeoff'), sq.c.track.label('takeoff_track'), null().label('landing'), null().label('landing_track'), null().label('duration')) \
        .filter(sq.c.is_takeoff == true()) \
        .filter(or_(sq.c.address != sq.c.address_next,
                    sq.c.is_takeoff_next == true()))

    # unite all
    union_query = complete_flight_query.union(split_start_query, split_landing_query, only_landings_query, only_starts_query) \
        .subquery()

    # get aircraft informations and sort all entries by the reference time
    logbook_query = session.query(union_query.c.reftime, union_query.c.address, union_query.c.takeoff, union_query.c.takeoff_track, union_query.c.landing, union_query.c.landing_track, union_query.c.duration, Flarm.registration, Flarm.aircraft) \
        .outerjoin(Flarm, union_query.c.address == Flarm.address) \
        .order_by(union_query.c.reftime)

    print('--- Logbook (' + airport_name + ') ---')
    none_datetime_replacer = lambda datetime_object: '--:--:--' if datetime_object is None else datetime_object.time()
    none_track_replacer = lambda track_object: '--' if track_object is None else round(track_object/10.0)
    none_timedelta_replacer = lambda timedelta_object: '--:--:--' if timedelta_object is None else timedelta_object
    none_registration_replacer = lambda registration_object, address: '[' + address + ']' if registration_object is None else registration_object
    none_aircraft_replacer = lambda aircraft_object: '(unknown)' if aircraft_object is None else aircraft_object
    for [reftime, address, takeoff, takeoff_track, landing, landing_track, duration, registration, aircraft] in logbook_query.all():
        print('%10s   %8s (%2s)   %8s (%2s)   %8s   %8s   %s' % (reftime.date(), none_datetime_replacer(takeoff), none_track_replacer(takeoff_track), none_datetime_replacer(landing), none_track_replacer(landing_track), none_timedelta_replacer(duration), none_registration_replacer(registration, address), none_aircraft_replacer(aircraft)))

if __name__ == '__main__':
    compute_takeoff_and_landing()
    get_logbook('Königsdorf', 47.83, 11.46, 601)

