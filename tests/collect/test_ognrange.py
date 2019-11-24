from datetime import date
import unittest

from tests.base import TestBaseDB, db

from app.model import AircraftBeacon, Receiver, ReceiverCoverage, Device
from app.collect.ognrange import update_entries


class TestOGNrange(TestBaseDB):
    def setUp(self):
        super().setUp()

        # Create basic data and insert
        self.dd0815 = Device(address="DD0815")
        self.dd4711 = Device(address="DD4711")

        self.r01 = Receiver(name="Koenigsdf")
        self.r02 = Receiver(name="Bene")

        db.session.add(self.dd0815)
        db.session.add(self.dd4711)
        db.session.add(self.r01)
        db.session.add(self.r02)

        db.session.commit()

        # Create beacons and insert
        self.ab01 = AircraftBeacon(
            name="FLRDD0815", receiver_name="Koenigsdf", timestamp="2017-12-10 10:00:00", location_mgrs_short="89ABC1267", altitude=800
        )
        self.ab02 = AircraftBeacon(
            name="FLRDD0815", receiver_name="Koenigsdf", timestamp="2017-12-10 10:00:01", location_mgrs_short="89ABC1267", altitude=850
        )
        db.session.add(self.ab01)
        db.session.add(self.ab02)
        db.session.commit()

    def test_update_receiver_coverage(self):
        update_entries(db.session, date=date(2017, 12, 10))

        coverages = db.session.query(ReceiverCoverage).all()
        self.assertEqual(len(coverages), 1)
        coverage = coverages[0]
        self.assertEqual(coverage.location_mgrs_short, "89ABC1267")
        self.assertEqual(coverage.receiver_id, self.r01.id)
        self.assertEqual(coverage.min_altitude, 800)
        self.assertEqual(coverage.max_altitude, 850)


if __name__ == "__main__":
    unittest.main()
