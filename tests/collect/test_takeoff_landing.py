import datetime
import unittest

from tests.base import TestBaseDB, db

from app.model import TakeoffLanding

from app.collect.logbook import update_takeoff_landings


class TestTakeoffLanding(TestBaseDB):
    def test_broken_rope(self):
        """The algorithm should detect one takeoff and one landing."""

        self.insert_airports_and_devices()
        self.insert_sender_positions_broken_rope()

        # find the takeoff and the landing
        update_takeoff_landings(start=datetime.datetime(2016, 7, 2, 0, 0, 0), end=datetime.datetime(2016, 7, 2, 23, 59, 59))
        takeoff_landing_query = db.session.query(TakeoffLanding).filter(db.between(TakeoffLanding.timestamp, datetime.datetime(2016, 7, 2, 0, 0, 0), datetime.datetime(2016, 7, 2, 23, 59, 59)))

        self.assertEqual(len(takeoff_landing_query.all()), 2)
        for entry in takeoff_landing_query.all():
            self.assertEqual(entry.airport.name, "Koenigsdorf")

        # we should not find the takeoff and the landing again
        update_takeoff_landings(start=datetime.datetime(2016, 7, 2, 0, 0, 0), end=datetime.datetime(2016, 7, 2, 23, 59, 59))
        self.assertEqual(len(takeoff_landing_query.all()), 2)

    def test_broken_rope_with_stall(self):
        """Here we have a broken rope where the glider passes again the threshold for take off."""

        self.insert_airports_and_devices()
        self.insert_sender_positions_broken_rope_with_stall()

        # find the takeoff and the landing
        update_takeoff_landings(start=datetime.datetime(2019, 4, 13, 0, 0, 0), end=datetime.datetime(2019, 4, 13, 23, 59, 59))
        takeoff_landings = db.session.query(TakeoffLanding).filter(db.between(TakeoffLanding.timestamp, datetime.datetime(2019, 4, 13, 0, 0, 0), datetime.datetime(2019, 4, 13, 23, 59, 59))).all()

        self.assertEqual(len(takeoff_landings), 2)
        for entry in takeoff_landings:
            self.assertEqual(entry.airport.name, "Koenigsdorf")


if __name__ == "__main__":
    unittest.main()
