import unittest

from tests.base import TestBaseDB, db

from app.model import AircraftBeacon
from app.collect.database import upsert


class TestDatabase(TestBaseDB):
    @unittest.skip("wip")
    def test_insert_duplicate_beacons(self):
        row1 = {"name": "FLRDD0815", "receiver_name": "Koenigsdf", "timestamp": "2019-01-26 11:51:00", "ground_speed": None}
        row2 = {"name": "FLRDD0815", "receiver_name": "Koenigsdf", "timestamp": "2019-01-26 11:52:00", "ground_speed": 0}
        row3 = {"name": "FLRDD0815", "receiver_name": "Koenigsdf", "timestamp": "2019-01-26 11:53:00", "ground_speed": 1}
        row4 = {"name": "FLRDD0815", "receiver_name": "Koenigsdf", "timestamp": "2019-01-26 11:54:00", "ground_speed": None}

        upsert(session=db.session, model=AircraftBeacon, rows=[row1, row2, row3, row4], update_cols=["ground_speed"])

        row5 = {"name": "FLRDD0815", "receiver_name": "Koenigsdf", "timestamp": "2019-01-26 11:51:00", "ground_speed": 2}
        row6 = {"name": "FLRDD0815", "receiver_name": "Koenigsdf", "timestamp": "2019-01-26 11:52:00", "ground_speed": 3}
        row7 = {"name": "FLRDD0815", "receiver_name": "Koenigsdf", "timestamp": "2019-01-26 11:53:00", "ground_speed": None}
        row8 = {"name": "FLRDD0815", "receiver_name": "Koenigsdf", "timestamp": "2019-01-26 11:54:00", "ground_speed": None}

        upsert(session=db.session, model=AircraftBeacon, rows=[row5, row6, row7, row8], update_cols=["ground_speed"])

        result = db.session.query(AircraftBeacon).order_by(AircraftBeacon.timestamp).all()
        self.assertEqual(result[0].ground_speed, 2)
        self.assertEqual(result[1].ground_speed, 3)
        self.assertEqual(result[2].ground_speed, 1)
        self.assertEqual(result[3].ground_speed, None)


if __name__ == "__main__":
    unittest.main()
