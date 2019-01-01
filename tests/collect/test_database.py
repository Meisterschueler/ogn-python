import unittest
import os

from ogn.model import AircraftBeacon, ReceiverBeacon, Device, Receiver, DeviceInfo
from ogn.collect.database import add_missing_devices, add_missing_receivers, import_ddb


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

    def tearDown(self):
        session = self.session
        session.execute("DELETE FROM device_infos")
        session.execute("DELETE FROM devices")
        session.execute("DELETE FROM receivers")
        session.execute("DELETE FROM aircraft_beacons")
        session.execute("DELETE FROM receiver_beacons")
        session.commit()

    def test_update_devices(self):
        session = self.session

        ab01 = AircraftBeacon(name='FLRDD4711', receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:00')
        rb01 = ReceiverBeacon(name='Bene', receiver_name='GLIDERN1', timestamp='2017-12-10 09:59:50')
        d01 = Device(address='DD4711')
        r01 = Receiver(name='Koenigsdf')
        session.bulk_save_objects([ab01, rb01, d01, r01])

        add_missing_devices(session)
        add_missing_receivers(session)

        aircraft_beacons = session.query(AircraftBeacon).all()
        self.assertEqual(len(aircraft_beacons), 1)
        aircraft_beacon = aircraft_beacons[0]
        self.assertEqual(aircraft_beacon.device.address, 'DD4711')
        self.assertEqual(aircraft_beacon.receiver.name, 'Koenigsdf')

        receiver_beacons = session.query(ReceiverBeacon).all()
        self.assertEqual(len(receiver_beacons), 1)
        receiver_beacon = receiver_beacons[0]
        self.assertEqual(receiver_beacon.receiver.name, 'Bene')

    def test_import_ddb_file(self):
        session = self.session

        import_ddb(session, path=os.path.dirname(__file__) + '/../custom_ddb.txt')

        device_infos = session.query(DeviceInfo).all()
        self.assertEqual(len(device_infos), 6)


if __name__ == '__main__':
    unittest.main()
