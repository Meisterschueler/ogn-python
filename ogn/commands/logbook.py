# -*- coding: utf-8 -*-

from datetime import timedelta

from sqlalchemy.sql import func, null
from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import true, false, label

from ogn.model import Device, TakeoffLanding, Airport

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
    print("New/recalculated takeoffs/landings: {}".format(counter))


@manager.arg('utc_delta_hours', help='delta hours to utc (for local time logs)')
@manager.command
def show(airport_name, utc_delta_hours=0):
    """Show a logbook for <airport_name>."""
    airport = session.query(Airport) \
        .filter(Airport.name == airport_name) \
        .first()

    if (airport is None):
        print('Airport "{}" not found.'.format(airport_name))
        return

    utc_timedelta = timedelta(hours=utc_delta_hours)

    # make a query with current, previous and next "takeoff_landing" event, so we can find complete flights
    sq = session.query(
        TakeoffLanding.device_id,
        func.lag(TakeoffLanding.device_id)
            .over(
                order_by=and_(func.date(TakeoffLanding.timestamp+utc_timedelta),
                              TakeoffLanding.device_id,
                              TakeoffLanding.timestamp+utc_timedelta))
            .label('device_id_prev'),
        func.lead(TakeoffLanding.device_id)
            .over(order_by=and_(func.date(TakeoffLanding.timestamp+utc_timedelta),
                                TakeoffLanding.device_id,
                                TakeoffLanding.timestamp+utc_timedelta))
            .label('device_id_next'),
        (TakeoffLanding.timestamp+utc_timedelta).label('timestamp'),
        func.lag(TakeoffLanding.timestamp)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp+utc_timedelta),
                                    TakeoffLanding.device_id,
                                    TakeoffLanding.timestamp+utc_timedelta))
                .label('timestamp_prev'),
        func.lead(TakeoffLanding.timestamp+utc_timedelta)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp+utc_timedelta),
                                    TakeoffLanding.device_id,
                                    TakeoffLanding.timestamp+utc_timedelta))
                .label('timestamp_next'),
        TakeoffLanding.track,
        func.lag(TakeoffLanding.track)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp+utc_timedelta),
                                    TakeoffLanding.device_id,
                                    TakeoffLanding.timestamp+utc_timedelta))
                .label('track_prev'),
        func.lead(TakeoffLanding.track)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp+utc_timedelta),
                                    TakeoffLanding.device_id,
                                    TakeoffLanding.timestamp+utc_timedelta))
                .label('track_next'),
        TakeoffLanding.is_takeoff,
        func.lag(TakeoffLanding.is_takeoff)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp+utc_timedelta),
                                    TakeoffLanding.device_id,
                                    TakeoffLanding.timestamp+utc_timedelta))
                .label('is_takeoff_prev'),
        func.lead(TakeoffLanding.is_takeoff)
                .over(order_by=and_(func.date(TakeoffLanding.timestamp+utc_timedelta),
                                    TakeoffLanding.device_id,
                                    TakeoffLanding.timestamp+utc_timedelta))
                .label('is_takeoff_next')) \
        .filter(TakeoffLanding.airport_id == airport.id) \
        .subquery()

    # find complete flights (with takeoff and landing) with duration < 1 day
    complete_flight_query = session.query(sq.c.timestamp.label('reftime'), sq.c.device_id.label('device_id'), sq.c.timestamp.label('takeoff'), sq.c.track.label('takeoff_track'), sq.c.timestamp_next.label('landing'), sq.c.track_next.label('landing_track'), label('duration', sq.c.timestamp_next - sq.c.timestamp)) \
        .filter(and_(sq.c.is_takeoff == true(), sq.c.is_takeoff_next == false())) \
        .filter(sq.c.device_id == sq.c.device_id_next) \
        .filter(sq.c.timestamp_next - sq.c.timestamp < timedelta(days=1))

    # split complete flights (with takeoff and landing) with duration > 1 day into one takeoff and one landing
    split_start_query = session.query(sq.c.timestamp.label('reftime'), sq.c.device_id.label('device_id'), sq.c.timestamp.label('takeoff'), sq.c.track.label('takeoff_track'), null().label('landing'), null().label('landing_track'), null().label('duration')) \
        .filter(and_(sq.c.is_takeoff == true(), sq.c.is_takeoff_next == false())) \
        .filter(sq.c.device_id == sq.c.device_id_next) \
        .filter(sq.c.timestamp_next - sq.c.timestamp >= timedelta(days=1))

    split_landing_query = session.query(sq.c.timestamp_next.label('reftime'), sq.c.device_id.label('device_id'), null().label('takeoff'), null().label('takeoff_track'), sq.c.timestamp_next.label('landing'), sq.c.track_next.label('landing_track'), null().label('duration')) \
        .filter(and_(sq.c.is_takeoff == true(), sq.c.is_takeoff_next == false())) \
        .filter(sq.c.device_id == sq.c.device_id_next) \
        .filter(sq.c.timestamp_next - sq.c.timestamp >= timedelta(days=1))

    # find landings without start
    only_landings_query = session.query(sq.c.timestamp.label('reftime'), sq.c.device_id.label('device_id'), null().label('takeoff'), null().label('takeoff_track'), sq.c.timestamp.label('landing'), sq.c.track_next.label('landing_track'), null().label('duration')) \
        .filter(sq.c.is_takeoff == false()) \
        .filter(or_(sq.c.device_id != sq.c.device_id_prev,
                    sq.c.is_takeoff_prev == false()))

    # find starts without landing
    only_starts_query = session.query(sq.c.timestamp.label('reftime'), sq.c.device_id.label('device_id'), sq.c.timestamp.label('takeoff'), sq.c.track.label('takeoff_track'), null().label('landing'), null().label('landing_track'), null().label('duration')) \
        .filter(sq.c.is_takeoff == true()) \
        .filter(or_(sq.c.device_id != sq.c.device_id_next,
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
        union_query.c.takeoff,
        union_query.c.takeoff_track,
        union_query.c.landing,
        union_query.c.landing_track,
        union_query.c.duration,
        Device) \
        .outerjoin(Device, union_query.c.device_id == Device.id) \
        .order_by(union_query.c.reftime)

    print('--- Logbook ({}) ---'.format(airport_name))

    def none_datetime_replacer(datetime_object):
        return '--:--:--' if datetime_object is None else datetime_object.time()

    def none_track_replacer(track_object):
        return '--' if track_object is None else round(track_object / 10.0)

    def none_timedelta_replacer(timedelta_object):
        return '--:--:--' if timedelta_object is None else timedelta_object

    def none_registration_replacer(device_object):
        return '[' + device_object.address + ']' if device_object.registration is None else device_object.registration

    def none_aircraft_replacer(device_object):
        return '(unknown)' if device_object.aircraft is None else device_object.aircraft

    for [reftime, takeoff, takeoff_track, landing, landing_track, duration, device] in logbook_query.all():
        print('%10s   %8s (%2s)   %8s (%2s)   %8s   %8s   %s' % (
            reftime.date(),
            none_datetime_replacer(takeoff),
            none_track_replacer(takeoff_track),
            none_datetime_replacer(landing),
            none_track_replacer(landing_track),
            none_timedelta_replacer(duration),
            none_registration_replacer(device),
            none_aircraft_replacer(device)))
