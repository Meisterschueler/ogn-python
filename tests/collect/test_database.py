import unittest
import os

from ogn.model import AircraftBeacon, Device
from ogn.collect.database import update_devices


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

        # Create basic data and insert
        self.ab00 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:00', aircraft_type=1, stealth=False, error_count=0, software_version=None, hardware_version=None, real_address=None)
        self.ab01 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:01', aircraft_type=1, stealth=False, error_count=0, software_version=0.26, hardware_version=None, real_address=None)
        self.ab02 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:02', aircraft_type=1, stealth=False, error_count=1, software_version=0.27, hardware_version=None, real_address=None)
        self.ab03 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:03', aircraft_type=1, stealth=False, error_count=0, software_version=None, hardware_version=5, real_address='DD1234')
        self.ab04 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:04', aircraft_type=1, stealth=False, error_count=0, software_version=0.25, hardware_version=123, real_address='DDxxxx')
        self.ab05 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:05', aircraft_type=1, stealth=False, error_count=0, software_version=None, hardware_version=None, real_address='DD0815')

    def tearDown(self):
        session = self.session
        session.execute("DELETE FROM device")
        session.execute("DELETE FROM receiver")
        session.execute("DELETE FROM aircraft_beacon")
        session.commit()

    def test_update_devices(self):
        session = self.session

        # Compute 1st beacon
        session.add(self.ab00)
        session.commit()

        update_devices(session)

        devices = session.query(Device).all()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].address, 'DD4711')
        self.assertEqual(devices[0].software_version, None)
        self.assertEqual(self.ab00.device_id, devices[0].id)

        # Compute 2nd beacon: changed software version
        session.add(self.ab01)
        session.commit()

        update_devices(session)
        devices = session.query(Device).all()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].address, 'DD4711')
        self.assertEqual(devices[0].software_version, 0.26)

        # Compute 3rd beacon: changed software version, but with error_count > 0
        session.add(self.ab02)
        session.commit()

        update_devices(session)
        devices = session.query(Device).all()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].address, 'DD4711')
        self.assertEqual(devices[0].software_version, 0.26)
        self.assertEqual(devices[0].hardware_version, None)
        self.assertEqual(devices[0].real_address, None)

        # Compute 4.-6. beacon
        session.add(self.ab03)
        session.add(self.ab05)  # order is not important
        session.add(self.ab04)
        session.commit()

        update_devices(session)
        devices = session.query(Device).all()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].address, 'DD4711')
        self.assertEqual(devices[0].software_version, 0.25)
        self.assertEqual(devices[0].hardware_version, 123)
        self.assertEqual(devices[0].real_address, 'DD0815')


if __name__ == '__main__':
    unittest.main()
