# -*- coding: utf-8 -*-

from datetime import timedelta, datetime

from manager import Manager
from ogn.collect.logbook import update_logbook
from ogn.collect.takeoff_landings import update_takeoff_landings
from ogn.commands.dbutils import session
from ogn.model import Device, DeviceInfo, TakeoffLanding, Airport, Logbook
from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func


manager = Manager()


@manager.command
def compute_takeoff_landing():
    """Compute takeoffs and landings."""
    print("Compute takeoffs and landings...")
    result = update_takeoff_landings.delay()
    counter = result.get()
    print("New takeoffs/landings: {}".format(counter))


@manager.command
def compute_logbook():
    """Compute logbook."""
    print("Compute logbook...")
    result = update_logbook.delay()
    counter = result.get()
    print("New logbook entries: {}".format(counter))


@manager.arg('date', help='date (format: yyyy-mm-dd)')
@manager.command
def show(airport_name, utc_delta_hours=0, date=None):
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
        or_args = [and_(TakeoffLanding.timestamp >= date,
                        TakeoffLanding.timestamp < date + timedelta(hours=24))]

    # get device info with highes priority
    sq2 = session.query(DeviceInfo.address, func.max(DeviceInfo.address_origin).label('address_origin')) \
        .group_by(DeviceInfo.address) \
        .subquery()

    sq3 = session.query(DeviceInfo.address, DeviceInfo.registration, DeviceInfo.aircraft) \
        .filter(and_(DeviceInfo.address == sq2.c.address, DeviceInfo.address_origin == sq2.c.address_origin)) \
        .subquery()

    # get all logbook entries and add device and airport infos
    takeoff_airport = aliased(Airport, name='takeoff_airport')
    landing_airport = aliased(Airport, name='landing_airport')
    logbook_query = session.query(func.row_number().over(order_by=Logbook.reftime).label('row_number'),
                                  Logbook,
                                  Device,
                                  sq3.c.registration,
                                  sq3.c.aircraft) \
        .filter(or_(Logbook.takeoff_airport_id == airport.id,
                    Logbook.landing_airport_id == airport.id)) \
        .filter(*or_args) \
        .outerjoin(takeoff_airport, Logbook.takeoff_airport_id == takeoff_airport.id) \
        .outerjoin(landing_airport, Logbook.landing_airport_id == landing_airport.id) \
        .outerjoin(Device, Logbook.device_id == Device.id) \
        .outerjoin(sq3, sq3.c.address == Device.address) \
        .order_by(Logbook.reftime)

    # ... and finally print out the logbook
    print('--- Logbook ({}) ---'.format(airport_name))

    def none_datetime_replacer(datetime_object):
        return '--:--:--' if datetime_object is None else datetime_object.time()

    def none_track_replacer(track_object):
        return '--' if track_object is None else round(track_object / 10.0)

    def none_timedelta_replacer(timedelta_object):
        return '--:--:--' if timedelta_object is None else timedelta_object

    def none_registration_replacer(device_object, registration_object):
        return '[' + device_object.address + ']' if registration_object is None else registration_object

    def none_aircraft_replacer(device_object, aircraft_object):
        return '(unknown)' if aircraft_object is None else aircraft_object

    def airport_marker(takeoff_airport_object, landing_airport_object):
        if takeoff_airport_object is not None and takeoff_airport_object.name is not airport.name:
            return ('FROM: {}'.format(takeoff_airport_object.name))
        elif landing_airport_object is not None and landing_airport_object.name is not airport.name:
            return ('TO: {}'.format(landing_airport_object.name))
        else:
            return ('')

    def none_altitude_replacer(altitude_object, airport_object):
        return "?" if altitude_object is None else "{:5d}m ({:+5d}m)".format(altitude_object, altitude_object - airport_object.altitude)

    for [row_number, logbook, device, registration, aircraft] in logbook_query.all():
        print('%3d. %10s   %8s (%2s)   %8s (%2s)   %8s  %15s %8s   %17s %20s' % (
            row_number,
            logbook.reftime.date(),
            none_datetime_replacer(logbook.takeoff_timestamp),
            none_track_replacer(logbook.takeoff_track),
            none_datetime_replacer(logbook.landing_timestamp),
            none_track_replacer(logbook.landing_track),
            none_timedelta_replacer(logbook.duration),
            none_altitude_replacer(logbook.max_altitude, logbook.takeoff_airport),
            none_registration_replacer(device, registration),
            none_aircraft_replacer(device, aircraft),
            airport_marker(logbook.takeoff_airport, logbook.landing_airport)))
