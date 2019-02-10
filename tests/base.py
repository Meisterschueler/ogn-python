import unittest
import os

os.environ['OGN_CONFIG_MODULE'] = 'config.test'


class TestBaseDB(unittest.TestCase):
    session = None
    engine = None

    @classmethod
    def setUpClass(cls):
        from ogn_python.commands.dbutils import engine, session
        cls.session = session
        cls.engine = engine

        from ogn_python.commands.database import drop
        drop(sure='y')

        from ogn_python.commands.database import init
        init()

    def setUp(self):
        self.session.execute("""
            DELETE FROM aircraft_beacons;
            DELETE FROM receiver_beacons;
            DELETE FROM takeoff_landings;
            DELETE FROM logbook;
        """)

    def tearDown(self):
        self.session.rollback()


if __name__ == '__main__':
    unittest.main()
