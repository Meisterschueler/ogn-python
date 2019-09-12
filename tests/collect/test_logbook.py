import datetime
import unittest

from tests.base import TestBaseDB, db

from app.model import Logbook, Airport, Device, TakeoffLanding
from app.collect.logbook import update_entries


class TestLogbook(TestBaseDB):
    def setUp(self):
        super().setUp()

        # Create basic data and insert
        self.dd0815 = Device(address="DD0815")
        self.dd4711 = Device(address="DD4711")

        self.koenigsdorf = Airport(name="Koenigsdorf")
        self.ohlstadt = Airport(name="Ohlstadt")

        db.session.add(self.dd0815)
        db.session.add(self.dd4711)
        db.session.add(self.koenigsdorf)
        db.session.add(self.ohlstadt)

        db.session.commit()

        # Prepare takeoff and landings
        self.takeoff_koenigsdorf_dd0815 = TakeoffLanding(is_takeoff=True, timestamp="2016-06-01 10:00:00", airport_id=self.koenigsdorf.id, device_id=self.dd0815.id)
        self.landing_koenigsdorf_dd0815 = TakeoffLanding(is_takeoff=False, timestamp="2016-06-01 10:05:00", airport_id=self.koenigsdorf.id, device_id=self.dd0815.id)
        self.landing_koenigsdorf_dd0815_later = TakeoffLanding(is_takeoff=False, timestamp="2016-06-02 10:05:00", airport_id=self.koenigsdorf.id, device_id=self.dd0815.id)
        self.takeoff_ohlstadt_dd4711 = TakeoffLanding(is_takeoff=True, timestamp="2016-06-01 10:00:00", airport_id=self.ohlstadt.id, device_id=self.dd4711.id)

    def get_logbook_entries(self):
        return db.session.query(Logbook).order_by(Logbook.takeoff_airport_id, Logbook.reftime).all()

    def test_single_takeoff(self):
        db.session.add(self.takeoff_koenigsdorf_dd0815)
        db.session.commit()

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].landing_airport_id, None)

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)

    def test_single_landing(self):
        db.session.add(self.landing_koenigsdorf_dd0815)
        db.session.commit()

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, None)
        self.assertEqual(entries[0].landing_airport_id, self.koenigsdorf.id)

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)

    def test_different_takeoffs(self):
        db.session.add(self.takeoff_koenigsdorf_dd0815)
        db.session.add(self.takeoff_ohlstadt_dd4711)
        db.session.commit()

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[1].takeoff_airport_id, self.ohlstadt.id)

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)

    def test_takeoff_and_landing(self):
        db.session.add(self.takeoff_koenigsdorf_dd0815)
        db.session.add(self.landing_koenigsdorf_dd0815)
        db.session.commit()

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].landing_airport_id, self.koenigsdorf.id)

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)

    def test_takeoff_and_landing_on_different_days(self):
        db.session.add(self.takeoff_koenigsdorf_dd0815)
        db.session.add(self.landing_koenigsdorf_dd0815_later)
        db.session.commit()

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        update_entries(session=db.session, date=datetime.date(2016, 6, 2))
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].reftime, self.takeoff_koenigsdorf_dd0815.timestamp)
        self.assertEqual(entries[1].landing_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[1].reftime, self.landing_koenigsdorf_dd0815_later.timestamp)

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)

    def test_update(self):
        db.session.add(self.takeoff_koenigsdorf_dd0815)
        db.session.commit()

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)

        db.session.add(self.landing_koenigsdorf_dd0815)
        db.session.commit()

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].landing_airport_id, self.koenigsdorf.id)

        db.session.add(self.takeoff_ohlstadt_dd4711)
        db.session.commit()

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[1].takeoff_airport_id, self.ohlstadt.id)

    def test_update_wrong_order(self):
        db.session.add(self.landing_koenigsdorf_dd0815)
        db.session.commit()

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, None)
        self.assertEqual(entries[0].landing_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].reftime, self.landing_koenigsdorf_dd0815.timestamp)

        db.session.add(self.takeoff_koenigsdorf_dd0815)
        db.session.commit()

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries = self.get_logbook_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].takeoff_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].landing_airport_id, self.koenigsdorf.id)
        self.assertEqual(entries[0].reftime, self.takeoff_koenigsdorf_dd0815.timestamp)

        update_entries(session=db.session, date=datetime.date(2016, 6, 1))
        entries2 = self.get_logbook_entries()
        self.assertEqual(entries, entries2)


if __name__ == "__main__":
    unittest.main()
