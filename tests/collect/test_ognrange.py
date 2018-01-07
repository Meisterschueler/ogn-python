import unittest
import os

from ogn.model import AircraftBeacon, Receiver, ReceiverCoverage, Device
from ogn.collect.ognrange import update_receiver_coverage


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
        self.dd0815 = Device(address='DD0815')
        self.dd4711 = Device(address='DD4711')

        self.r01 = Receiver(name='Koenigsdf')
        self.r02 = Receiver(name='Bene')

        session.add(self.dd0815)
        session.add(self.dd4711)
        session.add(self.r01)
        session.add(self.r02)

        session.commit()

        # Create beacons and insert
        self.ab01 = AircraftBeacon(device_id=self.dd0815.id, receiver_id=self.r01.id, timestamp='2017-12-10 10:00:00', location_mgrs='89ABC1234567890', altitude=800)
        self.ab02 = AircraftBeacon(device_id=self.dd0815.id, receiver_id=self.r01.id, timestamp='2017-12-10 10:00:01', location_mgrs='89ABC1299967999', altitude=850)
        session.add(self.ab01)
        session.add(self.ab02)
        session.commit()

    def tearDown(self):
        session = self.session
        session.execute("DELETE FROM aircraft_beacon")
        session.execute("DELETE FROM receiver_coverage")
        session.execute("DELETE FROM device")
        session.execute("DELETE FROM receiver")
        session.commit()

    def test_update_receiver_coverage(self):
        session = self.session

        update_receiver_coverage(session)

        coverages = session.query(ReceiverCoverage).all()
        self.assertEqual(len(coverages), 1)
        coverage = coverages[0]
        self.assertEqual(coverage.location_mgrs, '89ABC1267')
        self.assertEqual(coverage.receiver_id, self.r01.id)
        self.assertEqual(coverage.min_altitude, 800)
        self.assertEqual(coverage.max_altitude, 850)


if __name__ == '__main__':
    unittest.main()
