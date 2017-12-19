import unittest
import os

from ogn.model import AircraftBeacon, ReceiverBeacon, Device, Receiver, DeviceInfo
from ogn.collect.database import update_devices, update_receivers, import_ddb_file


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
        self.ab01 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:00', aircraft_type=1, stealth=False, error_count=0, software_version=None, hardware_version=None, real_address=None)
        self.ab02 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:01', aircraft_type=1, stealth=False, error_count=0, software_version=6.01, hardware_version=None, real_address=None)
        self.ab03 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:02', aircraft_type=1, stealth=False, error_count=1, software_version=6.02, hardware_version=None, real_address=None)
        self.ab04 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:03', aircraft_type=1, stealth=False, error_count=0, software_version=None, hardware_version=5, real_address='DD1234')
        self.ab05 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:04', aircraft_type=1, stealth=False, error_count=0, software_version=6.00, hardware_version=123, real_address='DDxxxx')
        self.ab06 = AircraftBeacon(receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:05', aircraft_type=1, stealth=False, error_count=0, software_version=None, hardware_version=None, real_address='DD0815')

        self.rb01 = ReceiverBeacon(name='Koenigsdf', timestamp='2017-12-10 09:55:00', altitude=601, version='0.2.5', platform='ARM')
        self.rb02 = ReceiverBeacon(name='Koenigsdf', timestamp='2017-12-10 10:00:00', altitude=601, version='0.2.7', platform='ARM')
        self.rb03 = ReceiverBeacon(name='Koenigsdf', timestamp='2017-12-10 10:05:00', altitude=601, version='0.2.6', platform='ARM')

    def tearDown(self):
        session = self.session
        session.execute("DELETE FROM device_info")
        session.execute("DELETE FROM device")
        session.execute("DELETE FROM receiver")
        session.execute("DELETE FROM aircraft_beacon")
        session.execute("DELETE FROM receiver_beacon")
        session.commit()

    def test_update_devices(self):
        session = self.session

        # Compute 1st beacon
        session.add(self.ab01)
        session.commit()

        update_devices(session)

        devices = session.query(Device).all()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].address, 'DD4711')
        self.assertEqual(devices[0].software_version, None)
        self.assertEqual(self.ab01.device_id, devices[0].id)

        # Compute 2nd beacon: changed software version
        session.add(self.ab02)
        session.commit()

        update_devices(session)
        devices = session.query(Device).all()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].address, 'DD4711')
        self.assertEqual(devices[0].software_version, 6.01)
        self.assertEqual(self.ab02.device_id, devices[0].id)

        # Compute 3rd beacon: changed software version, but with error_count > 0
        session.add(self.ab03)
        session.commit()

        update_devices(session)
        devices = session.query(Device).all()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].address, 'DD4711')
        self.assertEqual(devices[0].software_version, 6.01)
        self.assertEqual(devices[0].hardware_version, None)
        self.assertEqual(devices[0].real_address, None)
        self.assertEqual(self.ab03.device_id, devices[0].id)

        # Compute 4.-6. beacon
        session.add(self.ab04)
        session.add(self.ab06)  # order is not important
        session.add(self.ab05)
        session.commit()

        update_devices(session)
        devices = session.query(Device).all()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].address, 'DD4711')
        self.assertEqual(devices[0].software_version, 6.0)
        self.assertEqual(devices[0].hardware_version, 123)
        self.assertEqual(devices[0].real_address, 'DD0815')
        self.assertEqual(self.ab04.device_id, devices[0].id)
        self.assertEqual(self.ab05.device_id, devices[0].id)
        self.assertEqual(self.ab06.device_id, devices[0].id)

    def test_update_receivers(self):
        session = self.session

        # Compute beacons
        session.add(self.rb01)
        session.add(self.rb02)
        session.add(self.rb03)
        session.add(self.ab01)
        session.commit()

        update_receivers(session)

        receivers = session.query(Receiver).all()
        self.assertEqual(len(receivers), 1)
        self.assertEqual(receivers[0].name, 'Koenigsdf')
        self.assertEqual(receivers[0].altitude, 601)
        self.assertEqual(receivers[0].version, '0.2.6')
        self.assertEqual(self.rb01.receiver_id, receivers[0].id)
        self.assertEqual(self.rb02.receiver_id, receivers[0].id)
        self.assertEqual(self.rb03.receiver_id, receivers[0].id)
        self.assertEqual(self.ab01.receiver_id, receivers[0].id)

    def test_import_ddb_file(self):
        session = self.session

        import_ddb_file(session, path=os.path.dirname(__file__) + '/../custom_ddb.txt')

        device_infos = session.query(DeviceInfo).all()
        self.assertEqual(len(device_infos), 6)


if __name__ == '__main__':
    unittest.main()
