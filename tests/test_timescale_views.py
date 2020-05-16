import unittest

from tests.base import TestBaseDB, db

from app.model import AircraftBeacon


class TestDatabase(TestBaseDB):
    def test_view(self):
        from app.timescale_views import MyView

        stats = db.session.query(MyView).all()
        for stat in stats:
            print(stat)


if __name__ == "__main__":
    unittest.main()
