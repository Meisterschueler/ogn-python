import unittest
import os

from ogn.commands.bulkimport import convert_logfile, import_csv_logfile
from ogn.model import AircraftBeacon, ReceiverBeacon


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
        session.execute("DELETE FROM aircraft_beacons")
        session.execute("DELETE FROM receiver_beacons")
        session.commit()

    def test_convert_logfile(self):
        path = os.path.dirname(__file__)

        convert_logfile(path=path)

        os.remove(os.path.join(path, 'aircraft_beacons.csv_2016-09-21.gz'))
        os.remove(os.path.join(path, 'receiver_beacons.csv_2016-09-21.gz'))

    def test_import_csv_logfile(self):
        session = self.session

        path = os.path.dirname(__file__)

        convert_logfile(path=path)

        import_csv_logfile(path, 'aircraft_beacons.csv_2016-09-21.gz')
        import_csv_logfile(path, 'receiver_beacons.csv_2016-09-21.gz')

        os.remove(os.path.join(path, 'aircraft_beacons.csv_2016-09-21.gz'))
        os.remove(os.path.join(path, 'receiver_beacons.csv_2016-09-21.gz'))

        aircraft_beacons = session.query(AircraftBeacon).all()
        receiver_beacons = session.query(ReceiverBeacon).all()

        self.assertGreater(len(aircraft_beacons), 1)
        self.assertGreater(len(receiver_beacons), 1)
