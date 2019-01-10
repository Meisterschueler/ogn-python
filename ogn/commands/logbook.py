# -*- coding: utf-8 -*-

from datetime import datetime

from manager import Manager
from ogn.collect.logbook import update_logbook
from ogn.collect.takeoff_landings import update_takeoff_landings
from ogn.commands.dbutils import session
from ogn.model import Airport, Logbook
from sqlalchemy import or_, between
from sqlalchemy.sql import func
from tqdm import tqdm
from ogn.commands.database import get_database_days
from ogn.utils import date_to_timestamps

manager = Manager()


@manager.command
def compute_takeoff_landing(start=None, end=None):
    """Compute takeoffs and landings."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, '%Y-%m-%d'))
        result = update_takeoff_landings(session=session, date=single_date)


@manager.command
def compute_logbook(start=None, end=None):
    """Compute logbook."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, '%Y-%m-%d'))
        result = update_logbook(session=session, date=single_date)


@manager.arg('date', help='date (format: yyyy-mm-dd)')
@manager.command
def show(airport_name, date=None):
    """Show a logbook for <airport_name>."""
    airport = session.query(Airport) \
        .filter(Airport.name == airport_name) \
        .first()

    if (airport is None):
        print('Airport "{}" not found.'.format(airport_name))
        return

    or_args = []
    if date is not None:
        date = datetime.strptime(date, "%Y-%m-%d")
        (start, end) = date_to_timestamps(date)
        or_args = [between(Logbook.reftime, start, end)]

    # get all logbook entries and add device and airport infos
    logbook_query = session.query(func.row_number().over(order_by=Logbook.reftime).label('row_number'),
                                  Logbook) \
        .filter(*or_args) \
        .filter(or_(Logbook.takeoff_airport_id == airport.id,
                    Logbook.landing_airport_id == airport.id)) \
        .order_by(Logbook.reftime)

    # ... and finally print out the logbook
    print('--- Logbook ({}) ---'.format(airport_name))

    def none_datetime_replacer(datetime_object):
        return '--:--:--' if datetime_object is None else datetime_object.time()

    def none_track_replacer(track_object):
        return '--' if track_object is None else round(track_object / 10.0)

    def none_timedelta_replacer(timedelta_object):
        return '--:--:--' if timedelta_object is None else timedelta_object

    def none_registration_replacer(device_object):
        return '[' + device_object.address + ']' if len(device_object.infos) == 0 else device_object.infos[0].registration

    def none_aircraft_replacer(device_object):
        return '(unknown)' if len(device_object.infos) == 0 else device_object.infos[0].aircraft

    def airport_marker(logbook_object):
        if logbook_object.takeoff_airport is not None and logbook_object.takeoff_airport.name is not airport.name:
            return ('FROM: {}'.format(logbook_object.takeoff_airport.name))
        elif logbook_object.landing_airport is not None and logbook_object.landing_airport.name is not airport.name:
            return ('TO: {}'.format(logbook_object.landing_airport.name))
        else:
            return ('')

    def none_altitude_replacer(logbook_object):
        return "?" if logbook_object.max_altitude is None else "{:5d}m ({:+5d}m)".format(logbook_object.max_altitude, logbook_object.max_altitude - logbook_object.takeoff_airport.altitude)

    for [row_number, logbook] in logbook_query.all():
        print('%3d. %10s   %8s (%2s)   %8s (%2s)   %8s  %15s %8s   %17s %20s' % (
            row_number,
            logbook.reftime.date(),
            none_datetime_replacer(logbook.takeoff_timestamp),
            none_track_replacer(logbook.takeoff_track),
            none_datetime_replacer(logbook.landing_timestamp),
            none_track_replacer(logbook.landing_track),
            none_timedelta_replacer(logbook.duration),
            none_altitude_replacer(logbook),
            none_registration_replacer(logbook.device),
            none_aircraft_replacer(logbook.device),
            airport_marker(logbook)))
