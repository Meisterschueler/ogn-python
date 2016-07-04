import unittest
import os

from ogn.model import Logbook

from ogn.collect.logbook import compute_logbook_entries


class TestDB(unittest.TestCase):
    session = None
    engine = None
    app = None

    TAKEOFF_KOENIGSDF_DD0815       = "INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:00:00', TRUE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'"
    LANDING_KOENIGSDF_DD0815       = "INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:05:00', FALSE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'"
    LANDING_KOENIGSDF_DD0815_LATER = "INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-02 10:05:00', FALSE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'"
    TAKEOFF_OHLSTADT_DD4711        = "INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:00:00', TRUE FROM airport a, device d WHERE a.name='Ohlstadt' and d.address = 'DD4711'"

    def setUp(self):
        os.environ['OGN_CONFIG_MODULE'] = 'config.test'
        from ogn.commands.dbutils import engine, session
        self.session = session
        self.engine = engine

        from ogn.commands.database import init
        init()

        session.execute("INSERT INTO device(address) VALUES ('DD0815'), ('DD4711')")
        session.execute("INSERT INTO airport(name) VALUES ('Koenigsdorf'), ('Ohlstadt')")

    def tearDown(self):
        session = self.session
        session.execute("DELETE FROM takeoff_landing")
        session.execute("DELETE FROM logbook")
        session.execute("DELETE FROM device")
        session.execute("DELETE FROM airport")
        session.commit()
        pass

    def test_single_takeoff(self):
        session = self.session

        session.execute(self.TAKEOFF_KOENIGSDF_DD0815)
        session.commit()

        entries_changed = compute_logbook_entries(session)
        self.assertEqual(entries_changed, '0/1')

    def test_single_landing(self):
        session = self.session

        session.execute(self.LANDING_KOENIGSDF_DD0815)
        session.commit()

        entries_changed = compute_logbook_entries(session)
        self.assertEqual(entries_changed, '0/1')

    def test_different_takeoffs(self):
        session = self.session

        session.execute(self.TAKEOFF_KOENIGSDF_DD0815)
        session.execute(self.TAKEOFF_OHLSTADT_DD4711)
        session.commit()

        entries_changed = compute_logbook_entries(session)
        self.assertEqual(entries_changed, '0/2')

    def test_takeoff_and_landing(self):
        session = self.session

        session.execute(self.TAKEOFF_KOENIGSDF_DD0815)
        session.execute(self.LANDING_KOENIGSDF_DD0815)
        session.commit()

        entries_changed = compute_logbook_entries(session)
        self.assertEqual(entries_changed, '0/1')

    def test_takeoff_and_landing_on_different_days(self):
        session = self.session

        session.execute(self.TAKEOFF_KOENIGSDF_DD0815)
        session.execute(self.LANDING_KOENIGSDF_DD0815_LATER)
        session.commit()

        entries_changed = compute_logbook_entries(session)
        self.assertEqual(entries_changed, '0/2')

    def test_update(self):
        session = self.session

        session.execute(self.TAKEOFF_KOENIGSDF_DD0815)
        session.commit()

        entries_changed = compute_logbook_entries(session)
        self.assertEqual(entries_changed, '0/1')

        session.execute(self.LANDING_KOENIGSDF_DD0815)
        session.commit()

        entries_changed = compute_logbook_entries(session)
        self.assertEqual(entries_changed, '1/0')

        session.execute(self.TAKEOFF_OHLSTADT_DD4711)
        session.commit()

        entries_changed = compute_logbook_entries(session)
        self.assertEqual(entries_changed, '0/1')

    def test_update_wrong_order(self):
        session = self.session

        session.execute(self.LANDING_KOENIGSDF_DD0815)
        session.commit()

        entries_changed = compute_logbook_entries(session)
        self.assertEqual(entries_changed, '0/1')

        session.execute(self.TAKEOFF_KOENIGSDF_DD0815)
        session.commit()

        entries_changed = compute_logbook_entries(session)
        self.assertEqual(entries_changed, '1/0')

if __name__ == '__main__':
    unittest.main()
