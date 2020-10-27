import unittest

from tests.base import TestBaseDB, db

from app.model import AircraftBeacon


class TestDatabase(TestBaseDB):
    def test_view(self):
        from app.timescale_views import MyView

        self.insert_airports_and_devices()
        self.insert_aircraft_beacons_broken_rope()

        db.session.execute("REFRESH MATERIALIZED VIEW device_stats;")

        stats = db.session.query(MyView).all()
        for stat in stats:
            print(stat)


if __name__ == "__main__":
    unittest.main()
