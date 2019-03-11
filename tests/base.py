import unittest
import os

os.environ['OGN_CONFIG_MODULE'] = 'config/test.py'

from ogn_python import db   # noqa: E402


class TestBaseDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.session.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
        db.session.commit()
        db.drop_all()
        db.create_all()

    def setUp(self):
        pass

    def tearDown(self):
        db.session.execute("""
            DELETE FROM aircraft_beacons;
            DELETE FROM receiver_beacons;
            DELETE FROM takeoff_landings;
            DELETE FROM logbook;
        """)


if __name__ == '__main__':
    unittest.main()
