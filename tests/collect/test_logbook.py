import unittest
import os

from ogn.model import Logbook

from ogn.collect.logbook import compute_logbook_entries


class TestDB(unittest.TestCase):
    session = None
    engine = None
    app = None

    def setUp(self):
        os.environ['OGN_CONFIG_MODULE'] = 'config.test'
        from ogn.commands.dbutils import engine, session
        self.session = session
        self.engine = engine

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

    def count_logbook_entries(self):
        session = self.session
        logbook_query = session.query(Logbook)
        i = 0
        for logbook in logbook_query.all():
            i = i + 1
            print("{} {} {} {} {} {}".format(logbook.id, logbook.device_id, logbook.takeoff_airport_id, logbook.takeoff_timestamp, logbook.landing_airport_id, logbook.landing_timestamp))

        return i

    def test_single_takeoff(self):
        session = self.session

        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:00:00', TRUE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'")
        session.commit()

        compute_logbook_entries(session)
        self.assertEqual(self.count_logbook_entries(), 1)

    def test_single_landing(self):
        session = self.session

        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:00:00', FALSE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'")
        session.commit()

        compute_logbook_entries(session)
        self.assertEqual(self.count_logbook_entries(), 1)

    def test_different_takeoffs(self):
        session = self.session

        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:00:00', TRUE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'")
        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:00:00', TRUE FROM airport a, device d WHERE a.name='Ohlstadt' and d.address = 'DD4711'")
        session.commit()

        compute_logbook_entries(session)
        self.assertEqual(self.count_logbook_entries(), 2)

    def test_takeoff_and_landing(self):
        session = self.session

        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:00:00', TRUE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'")
        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:05:00', FALSE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'")
        session.commit()

        compute_logbook_entries(session)
        self.assertEqual(self.count_logbook_entries(), 1)

    def test_takeoff_and_landing_on_different_days(self):
        session = self.session

        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:00:00', TRUE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'")
        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-02 10:05:00', FALSE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'")
        session.commit()

        compute_logbook_entries(session)
        self.assertEqual(self.count_logbook_entries(), 2)

    def test_update(self):
        session = self.session

        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:00:00', TRUE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'")
        session.commit()
        compute_logbook_entries(session)
        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:05:00', FALSE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'")
        session.commit()
        compute_logbook_entries(session)

        self.assertEqual(self.count_logbook_entries(), 1)

    def test_update_wrong_order(self):
        session = self.session

        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:05:00', FALSE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'")
        session.commit()
        compute_logbook_entries(session)
        session.execute("INSERT INTO takeoff_landing(device_id, airport_id, timestamp, is_takeoff) SELECT d.id, a.id, '2016-06-01 10:00:00', TRUE FROM airport a, device d WHERE a.name='Koenigsdorf' and d.address = 'DD0815'")
        session.commit()
        compute_logbook_entries(session)

        self.assertEqual(self.count_logbook_entries(), 1)

if __name__ == '__main__':
    unittest.main()
