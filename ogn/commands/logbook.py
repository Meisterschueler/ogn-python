# -*- coding: utf-8 -*-

from datetime import timedelta

from sqlalchemy.sql import func, null
from sqlalchemy import and_, or_, between
from sqlalchemy.sql.expression import true, false, label

from ogn.model import Device, TakeoffLanding

from ogn.commands.dbutils import session
from ogn.collect.logbook import compute_takeoff_and_landing

from manager import Manager
manager = Manager()


@manager.command
def compute():
    """Compute takeoffs and landings."""
    print("Compute takeoffs and landings...")
    result = compute_takeoff_and_landing.delay()
    counter = result.get()
    print("New/recalculated takeoffs/landings: %s" % counter)


@manager.command
def show(airport_name, latitude, longitude, altitude):
    """Show a logbook for <airport_name> located at given position."""
    latitude = float(latitude)
    longitude = float(longitude)
    altitude = float(altitude)
    # get_logbook('Königsdorf', 47.83, 11.46, 601)
    latmin = latitude - 0.15
    latmax = latitude + 0.15
    lonmin = longitude - 0.15
    lonmax = longitude + 0.15
    max_altitude = altitude + 200

    # make a query with current, previous and next "takeoff_landing" event, so we can find complete flights
    sq = session.query(
        TakeoffLanding.address,
        func.lag(TakeoffLanding.address)
            .over(
                order_by=and_(func.date(TakeoffLanding.timestamp),
                              TakeoffLanding.address,
                              TakeoffLanding.timestamp))
            .label('address_prev'),
        func.lead(TakeoffLanding.address)
            .over(order_by=and_(func.date(TakeoffLanding.timestamp),
                                TakeoffLanding.address,
                                TakeoffLanding.timestamp))
            .label('address_next'),
        TakeoffLanding.timestamp,
        func.lag(TakeoffLanding.timestamp)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp),
                                    TakeoffLanding.address,
                                    TakeoffLanding.timestamp))
                .label('timestamp_prev'),
        func.lead(TakeoffLanding.timestamp)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp),
                                    TakeoffLanding.address,
                                    TakeoffLanding.timestamp))
                .label('timestamp_next'),
        TakeoffLanding.track,
        func.lag(TakeoffLanding.track)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp),
                                    TakeoffLanding.address,
                                    TakeoffLanding.timestamp))
                .label('track_prev'),
        func.lead(TakeoffLanding.track)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp),
                                    TakeoffLanding.address,
                                    TakeoffLanding.timestamp))
                .label('track_next'),
        TakeoffLanding.is_takeoff,
        func.lag(TakeoffLanding.is_takeoff)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp),
                                    TakeoffLanding.address,
                                    TakeoffLanding.timestamp))
                .label('is_takeoff_prev'),
        func.lead(TakeoffLanding.is_takeoff)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp),
                                    TakeoffLanding.address,
                                    TakeoffLanding.timestamp))
                .label('is_takeoff_next')) \
        .filter(and_(between(TakeoffLanding.latitude, latmin, latmax),
                     between(TakeoffLanding.longitude, lonmin, lonmax))) \
        .filter(TakeoffLanding.altitude < max_altitude) \
        .subquery()

    # find complete flights (with takeoff and landing) with duration < 1 day
    complete_flight_query = session.query(sq.c.timestamp.label('reftime'), sq.c.address.label('address'), sq.c.timestamp.label('takeoff'), sq.c.track.label('takeoff_track'), sq.c.timestamp_next.label('landing'), sq.c.track_next.label('landing_track'), label('duration', sq.c.timestamp_next - sq.c.timestamp)) \
        .filter(and_(sq.c.is_takeoff == true(), sq.c.is_takeoff_next == false())) \
        .filter(sq.c.address == sq.c.address_next) \
        .filter(sq.c.timestamp_next - sq.c.timestamp < timedelta(days=1))

    # split complete flights (with takeoff and landing) with duration > 1 day into one takeoff and one landing
    split_start_query = session.query(sq.c.timestamp.label('reftime'), sq.c.address.label('address'), sq.c.timestamp.label('takeoff'), sq.c.track.label('takeoff_track'), null().label('landing'), null().label('landing_track'), null().label('duration')) \
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
    union_query = complete_flight_query.union(
        split_start_query,
        split_landing_query,
        only_landings_query,
        only_starts_query) \
        .subquery()

    # get aircraft informations and sort all entries by the reference time
    logbook_query = session.query(
        union_query.c.reftime,
        union_query.c.address,
        union_query.c.takeoff,
        union_query.c.takeoff_track,
        union_query.c.landing,
        union_query.c.landing_track,
        union_query.c.duration,
        Device.registration,
        Device.aircraft) \
        .outerjoin(Device, union_query.c.address == Device.address) \
        .order_by(union_query.c.reftime)

    print('--- Logbook (%s) ---' % airport_name)

    def none_datetime_replacer(datetime_object):
        '--:--:--' if datetime_object is None else datetime_object.time()

    def none_track_replacer(track_object):
        '--' if track_object is None else round(track_object / 10.0)

    def none_timedelta_replacer(timedelta_object):
        '--:--:--' if timedelta_object is None else timedelta_object

    def none_registration_replacer(registration_object, address):
        '[' + address + ']' if registration_object is None else registration_object

    def none_aircraft_replacer(aircraft_object):
        '(unknown)' if aircraft_object is None else aircraft_object

    for [reftime, address, takeoff, takeoff_track, landing, landing_track, duration, registration, aircraft] in logbook_query.all():
        print('%10s   %8s (%2s)   %8s (%2s)   %8s   %8s   %s' % (
            reftime.date(),
            none_datetime_replacer(takeoff),
            none_track_replacer(takeoff_track),
            none_datetime_replacer(landing),
            none_track_replacer(landing_track),
            none_timedelta_replacer(duration),
            none_registration_replacer(registration, address),
            none_aircraft_replacer(aircraft)))
