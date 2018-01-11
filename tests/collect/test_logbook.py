import unittest
import os

from ogn.model import Logbook, Airport, Device, TakeoffLanding
from ogn.collect.logbook import update_logbook


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

        self.koenigsdorf = Airport(name='Koenigsdorf')
        self.ohlstadt = Airport(name='Ohlstadt')

        session.add(self.dd0815)
        session.add(self.dd4711)
        session.add(self.koenigsdorf)
        session.add(self.ohlstadt)

        session.commit()

        # Prepare takeoff and landings
        self.takeoff_koenigsdorf_dd0815 = TakeoffLanding(is_takeoff=True, timestamp='2016-06-01 10:00:00', airport_id=self.koenigsdorf.id, device_id=self.dd0815.id)
        self.landing_koenigsdorf_dd0815 = TakeoffLanding(is_takeoff=False, timestamp='2016-06-01 10:05:00', airport_id=self.koenigsdorf.id, device_id=self.dd0815.id)
        self.landing_koenigsdorf_dd0815_later = TakeoffLanding(is_takeoff=False, timestamp='2016-06-02 10:05:00', airport_id=self.koenigsdorf.id, device_id=self.dd0815.id)
        self.takeoff_ohlstadt_dd4711 = TakeoffLanding(is_takeoff=True, timestamp='2016-06-01 10:00:00', airport_id=self.ohlstadt.id, device_id=self.dd4711.id)

    def tearDown(self):
        session = self.session
        session.execute("DELETE FROM takeoff_landings")
        session.execute("DELETE FROM logbook")
        session.execute("DELETE FROM devices")
        session.execute("DELETE FROM airports")
        session.commit()

    def get_logbook_entries(self):
        session = self.session
        return session.query(Logbook).order_by(Logbook.takeoff_airport_id, Logbook.reftime).all()

    def test_single_takeoff(self):
        session = self.session

        session.add(self.takeoff_koenigsdorf_dd0815)
        session.commit()

        update_logbook(session)
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].landing_airport_id, None)

        update_logbook(session)
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)

    def test_single_landing(self):
        session = self.session

        session.add(self.landing_koenigsdorf_dd0815)
        session.commit()

        update_logbook(session)
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, None)
        self.assertEqual(entries[0].landing_airport_id, self.koenigsdorf.id)

        update_logbook(session)
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)

    def test_different_takeoffs(self):
        session = self.session

        session.add(self.takeoff_koenigsdorf_dd0815)
        session.add(self.takeoff_ohlstadt_dd4711)
        session.commit()

        update_logbook(session)
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[1].takeoff_airport_id, self.ohlstadt.id)

        update_logbook(session)
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)

    def test_takeoff_and_landing(self):
        session = self.session

        session.add(self.takeoff_koenigsdorf_dd0815)
        session.add(self.landing_koenigsdorf_dd0815)
        session.commit()

        update_logbook(session)
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].landing_airport_id, self.koenigsdorf.id)

        update_logbook(session)
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)

    def test_takeoff_and_landing_on_different_days(self):
        session = self.session

        session.add(self.takeoff_koenigsdorf_dd0815)
        session.add(self.landing_koenigsdorf_dd0815_later)
        session.commit()

        update_logbook(session)
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].reftime, self.takeoff_koenigsdorf_dd0815.timestamp)
        self.assertEqual(entries[1].landing_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[1].reftime, self.landing_koenigsdorf_dd0815_later.timestamp)

        update_logbook(session)
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)

    def test_update(self):
        session = self.session

        session.add(self.takeoff_koenigsdorf_dd0815)
        session.commit()

        update_logbook(session)
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)

        session.add(self.landing_koenigsdorf_dd0815)
        session.commit()

        update_logbook(session)
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].landing_airport_id, self.koenigsdorf.id)

        session.add(self.takeoff_ohlstadt_dd4711)
        session.commit()

        update_logbook(session)
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[1].takeoff_airport_id, self.ohlstadt.id)

    def test_update_wrong_order(self):
        session = self.session

        session.add(self.landing_koenigsdorf_dd0815)
        session.commit()

        update_logbook(session)
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, None)
        self.assertEqual(entries[0].landing_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].reftime, self.landing_koenigsdorf_dd0815.timestamp)

        session.add(self.takeoff_koenigsdorf_dd0815)
        session.commit()

        update_logbook(session)
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].landing_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].reftime, self.takeoff_koenigsdorf_dd0815.timestamp)

        update_logbook(session)
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)


if __name__ == '__main__':
    unittest.main()
