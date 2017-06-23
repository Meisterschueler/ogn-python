from sqlalchemy.sql import func
from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased

from ogn.model import AircraftBeacon, Device

from ogn.commands.dbutils import session

from aerofiles.igc import Writer

import datetime
import re


from manager import Manager
manager = Manager()


@manager.arg('address', help='address (flarm id)')
@manager.arg('date', help='date (format: yyyy-mm-dd)')
@manager.command
def write(address, date):
    """Export igc file for <address> at <date>."""
    if not re.match('.{6}', address):
        print("Address {} not valid.".format(address))
        return

    if not re.match('\d{4}-\d{2}-\d{2}', date):
        print("Date {} not valid.".format(date))
        return

    device_id = session.query(Device.id) \
        .filter(Device.address == address) \
        .first()

    if (device_id is None):
        print ("Device with address '{}' not found.".format(address))
        return

    with open('sample.igc', 'wb') as fp:
        writer = Writer(fp)

        writer.write_headers({
            'manufacturer_code': 'OGN',
            'logger_id': 'OGN',
            'date': datetime.date(1987, 2, 24),
            'fix_accuracy': 50,
            'pilot': 'Konstantin Gruendger',
            'copilot': '',
            'glider_type': 'Duo Discus',
            'glider_id': 'D-KKHH',
            'firmware_version': '2.2',
            'hardware_version': '2',
            'logger_type': 'LXNAVIGATION,LX8000F',
            'gps_receiver': 'uBLOX LEA-4S-2,16,max9000m',
            'pressure_sensor': 'INTERSEMA,MS5534A,max10000m',
            'competition_id': '2H',
            'competition_class': 'Doubleseater',
        })

        points = session.query(AircraftBeacon) \
            .filter(AircraftBeacon.device_id == device_id) \
            .filter(AircraftBeacon.timestamp > date + ' 00:00:00') \
            .filter(AircraftBeacon.timestamp < date + ' 23:59:59') \
            .order_by(AircraftBeacon.timestamp)

        for point in points.all():
            writer.write_fix(
                point.timestamp.time(),
                latitude=point.location.latitude,
                longitude=point.location.longitude,
                valid=True,
                pressure_alt=point.altitude,
                gps_alt=point.altitude,
            )
