import unittest
import os
from datetime import datetime, date

from ogn.model import AircraftBeacon, ReceiverBeacon, Receiver, Device, DeviceStats

from ogn.collect.stats import update_devices


class TestDB(unittest.TestCase):
    session = None
    engine = None
    app = None

    def setUp(self):
        os.environ['OGN_CONFIG_MODULE'] = 'config.test'
        from ogn.commands.dbutils import engine, session
        self.session = session
        self.engine = engine

        from ogn.commands.database import init
        init()

        # Prepare Beacons
        self.ab01 = AircraftBeacon(name='FLRDD4711', receiver_name='Koenigsdf', timestamp='2017-12-10 10:00:01')
        self.ab02 = AircraftBeacon(name='FLRDD4711', receiver_name='Koenigsdf', timestamp='2017-12-10 10:00:02')
        self.ab03 = AircraftBeacon(name='FLRDD4711', receiver_name='Koenigsdf', timestamp='2017-12-10 10:00:03')
        self.ab04 = AircraftBeacon(name='FLRDD4711', receiver_name='Koenigsdf', timestamp='2017-12-10 10:00:04')
        self.ab05 = AircraftBeacon(name='FLRDD4711', receiver_name='Koenigsdf', timestamp='2017-12-10 10:00:05')
        self.ab06 = AircraftBeacon(name='FLRDD4711', receiver_name='Koenigsdf', timestamp='2017-12-10 10:00:05')

        self.rb01 = ReceiverBeacon(name='Koenigsdf', receiver_name='GLIDERN1', timestamp='2017-12-10 09:55:00', altitude=601, version='0.2.5', platform='ARM')
        self.rb02 = ReceiverBeacon(name='Koenigsdf', receiver_name='GLIDERN1', timestamp='2017-12-10 10:00:00', altitude=601, version='0.2.7', platform='ARM')
        self.rb03 = ReceiverBeacon(name='Koenigsdf', receiver_name='GLIDERN1', timestamp='2017-12-10 10:05:00', altitude=601, version='0.2.6', platform='ARM')

        self.r01 = Receiver(name='Koenigsdf')
        self.r02 = Receiver(name='Bene')

        self.d01 = Device(address='DD4711')

        session.add(self.r01)
        session.add(self.d01)
        session.commit()

    def tearDown(self):
        session = self.session
        session.execute("DELETE FROM device_infos")
        session.execute("DELETE FROM device_stats")
        session.execute("DELETE FROM devices")
        session.execute("DELETE FROM receivers")
        session.execute("DELETE FROM aircraft_beacons")
        session.execute("DELETE FROM receiver_beacons")
        session.commit()

    def test_update_devices(self):
        session = self.session

        # Compute 1st beacon
        self.ab01.device = self.d01
        self.ab01.receiver = self.r01
        session.add(self.ab01)
        session.commit()

        update_devices(session)

        devicestats = session.query(DeviceStats).all()
        self.assertEqual(len(devicestats), 1)
        self.assertEqual(devicestats[0].device, self.d01)

        self.assertEqual(devicestats[0].max_altitude, None)
        self.assertEqual(devicestats[0].receiver_count, 1)
        self.assertEqual(devicestats[0].aircraft_beacon_count, 1)
        self.assertEqual(devicestats[0].date, datetime.strptime('2017-12-10', '%Y-%m-%d').date())
        self.assertEqual(devicestats[0].firstseen, datetime(2017, 12, 10, 10, 0, 1))
        self.assertEqual(devicestats[0].lastseen, datetime(2017, 12, 10, 10, 0, 1))
        self.assertEqual(devicestats[0].aircraft_type, None)
        self.assertEqual(devicestats[0].stealth, None)
        self.assertEqual(devicestats[0].software_version, None)
        self.assertEqual(devicestats[0].hardware_version, None)
        self.assertEqual(devicestats[0].real_address, None)

        # Compute 2nd beacon: set altitude, aircraft_type and stealth
        self.ab02.device = self.d01
        self.ab02.receiver = self.r01
        self.ab02.altitude = 200
        self.ab02.aircraft_type = 3
        self.ab02.stealth = False
        session.add(self.ab02)
        session.commit()

        update_devices(session, date='2017-12-10')

        devicestats = session.query(DeviceStats).all()
        self.assertEqual(len(devicestats), 1)
        self.assertEqual(devicestats[0].device, self.d01)

        self.assertEqual(devicestats[0].max_altitude, 200)
        self.assertEqual(devicestats[0].receiver_count, 1)
        self.assertEqual(devicestats[0].aircraft_beacon_count, 2)
        self.assertEqual(devicestats[0].date, datetime.strptime('2017-12-10', '%Y-%m-%d').date())
        self.assertEqual(devicestats[0].firstseen, datetime(2017, 12, 10, 10, 0, 1))
        self.assertEqual(devicestats[0].lastseen, datetime(2017, 12, 10, 10, 0, 2))
        self.assertEqual(devicestats[0].aircraft_type, 3)
        self.assertEqual(devicestats[0].stealth, False)
        self.assertEqual(devicestats[0].software_version, None)
        self.assertEqual(devicestats[0].hardware_version, None)
        self.assertEqual(devicestats[0].real_address, None)

        # Compute 3rd beacon: changed software version, but with error_count > 0
        self.ab03.device = self.d01
        self.ab03.receiver = self.r01
        self.ab03.error_count = 1
        self.ab03.software_version = 6.01
        session.add(self.ab03)
        session.commit()

        update_devices(session, date='2017-12-10')

        devicestats = session.query(DeviceStats).all()
        self.assertEqual(len(devicestats), 1)
        self.assertEqual(devicestats[0].device, self.d01)

        self.assertEqual(devicestats[0].max_altitude, 200)
        self.assertEqual(devicestats[0].receiver_count, 1)
        self.assertEqual(devicestats[0].aircraft_beacon_count, 2)
        self.assertEqual(devicestats[0].date, datetime.strptime('2017-12-10', '%Y-%m-%d').date())
        self.assertEqual(devicestats[0].firstseen, datetime(2017, 12, 10, 10, 0, 1))
        self.assertEqual(devicestats[0].lastseen, datetime(2017, 12, 10, 10, 0, 2))
        self.assertEqual(devicestats[0].aircraft_type, 3)
        self.assertEqual(devicestats[0].stealth, False)
        self.assertEqual(devicestats[0].software_version, None)
        self.assertEqual(devicestats[0].hardware_version, None)
        self.assertEqual(devicestats[0].real_address, None)

        # Compute 4. beacon: another receiver, greater altitude, software_version, hardware_version, real_address
        self.ab04.device = self.d01
        self.ab04.receiver = self.r02
        self.ab04.altitude = 250
        self.ab04.software_version = 6.01
        self.ab04.hardware_version = 15
        self.ab04.real_address = 'DDALFA'
        session.add(self.ab04)
        session.commit()

        update_devices(session, date='2017-12-10')

        devicestats = session.query(DeviceStats).all()
        self.assertEqual(len(devicestats), 1)
        self.assertEqual(devicestats[0].device, self.d01)

        self.assertEqual(devicestats[0].max_altitude, 250)
        self.assertEqual(devicestats[0].receiver_count, 2)
        self.assertEqual(devicestats[0].aircraft_beacon_count, 3)
        self.assertEqual(devicestats[0].date, datetime.strptime('2017-12-10', '%Y-%m-%d').date())
        self.assertEqual(devicestats[0].firstseen, datetime(2017, 12, 10, 10, 0, 1))
        self.assertEqual(devicestats[0].lastseen, datetime(2017, 12, 10, 10, 0, 4))
        self.assertEqual(devicestats[0].aircraft_type, 3)
        self.assertEqual(devicestats[0].stealth, False)
        self.assertEqual(devicestats[0].software_version, 6.01)
        self.assertEqual(devicestats[0].hardware_version, 15)
        self.assertEqual(devicestats[0].real_address, 'DDALFA')

        # Compute 5. beacon: lower altitude, stealth
        self.ab05.device = self.d01
        self.ab05.receiver = self.r02
        self.ab05.altitude = 100
        self.ab05.stealth = True
        session.add(self.ab05)
        session.commit()

        update_devices(session, date='2017-12-10')

        devicestats = session.query(DeviceStats).all()
        self.assertEqual(len(devicestats), 1)
        self.assertEqual(devicestats[0].device, self.d01)

        self.assertEqual(devicestats[0].max_altitude, 250)
        self.assertEqual(devicestats[0].receiver_count, 2)
        self.assertEqual(devicestats[0].aircraft_beacon_count, 4)
        self.assertEqual(devicestats[0].date, datetime.strptime('2017-12-10', '%Y-%m-%d').date())
        self.assertEqual(devicestats[0].firstseen, datetime(2017, 12, 10, 10, 0, 1))
        self.assertEqual(devicestats[0].lastseen, datetime(2017, 12, 10, 10, 0, 5))
        self.assertEqual(devicestats[0].aircraft_type, 3)
        self.assertEqual(devicestats[0].stealth, True)
        self.assertEqual(devicestats[0].software_version, 6.01)
        self.assertEqual(devicestats[0].hardware_version, 15)
        self.assertEqual(devicestats[0].real_address, 'DDALFA')

        # Compute 6. beacon: beacon from past, greater altitude, newer version
        self.ab06.device = self.d01
        self.ab06.receiver = self.r02
        self.ab06.timestamp = datetime(2017, 12, 10, 9, 59, 50)
        self.ab06.altitude = 300
        self.ab06.software_version = 6.02
        session.add(self.ab06)
        session.commit()

        update_devices(session, date='2017-12-10')

        devicestats = session.query(DeviceStats).all()
        self.assertEqual(len(devicestats), 1)
        self.assertEqual(devicestats[0].device, self.d01)

        self.assertEqual(devicestats[0].max_altitude, 300)
        self.assertEqual(devicestats[0].receiver_count, 2)
        self.assertEqual(devicestats[0].aircraft_beacon_count, 5)
        self.assertEqual(devicestats[0].date, datetime.strptime('2017-12-10', '%Y-%m-%d').date())
        self.assertEqual(devicestats[0].firstseen, datetime(2017, 12, 10, 9, 59, 50))
        self.assertEqual(devicestats[0].lastseen, datetime(2017, 12, 10, 10, 0, 5))
        self.assertEqual(devicestats[0].aircraft_type, 3)
        self.assertEqual(devicestats[0].stealth, True)
        self.assertEqual(devicestats[0].software_version, 6.01)
        self.assertEqual(devicestats[0].hardware_version, 15)
        self.assertEqual(devicestats[0].real_address, 'DDALFA')


if __name__ == '__main__':
    unittest.main()
