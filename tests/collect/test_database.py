import unittest

from tests.base import TestBaseDB

from ogn.model import AircraftBeacon, ReceiverBeacon, Device, Receiver
from ogn.collect.database import add_missing_devices, add_missing_receivers, upsert


class TestDatabase(TestBaseDB):
    def test_update_devices(self):
        session = self.session

        ab01 = AircraftBeacon(name='FLRDD4711', receiver_name='Koenigsdf', address='DD4711', timestamp='2017-12-10 10:00:00')
        rb01 = ReceiverBeacon(name='Bene', receiver_name='GLIDERN1', timestamp='2017-12-10 09:59:50')
        d01 = Device(address='DD4711')
        r01 = Receiver(name='Koenigsdf')
        session.bulk_save_objects([ab01, rb01, d01, r01])

        add_missing_devices(session)
        add_missing_receivers(session)

        aircraft_beacons = session.query(AircraftBeacon).all()
        self.assertEqual(len(aircraft_beacons), 1)
        aircraft_beacon = aircraft_beacons[0]
        self.assertEqual(aircraft_beacon.device.address, 'DD4711')
        self.assertEqual(aircraft_beacon.receiver.name, 'Koenigsdf')

        receiver_beacons = session.query(ReceiverBeacon).all()
        self.assertEqual(len(receiver_beacons), 1)
        receiver_beacon = receiver_beacons[0]
        self.assertEqual(receiver_beacon.receiver.name, 'Bene')

    def test_insert_duplicate_beacons(self):
        session = self.session

        row1 = {'name': 'FLRDD0815', 'receiver_name': 'Koenigsdf', 'timestamp': '2019-01-26 11:51:00', 'ground_speed': None}
        row2 = {'name': 'FLRDD0815', 'receiver_name': 'Koenigsdf', 'timestamp': '2019-01-26 11:52:00', 'ground_speed': 0}
        row3 = {'name': 'FLRDD0815', 'receiver_name': 'Koenigsdf', 'timestamp': '2019-01-26 11:53:00', 'ground_speed': 1}
        row4 = {'name': 'FLRDD0815', 'receiver_name': 'Koenigsdf', 'timestamp': '2019-01-26 11:54:00', 'ground_speed': None}

        upsert(session=session, model=AircraftBeacon, rows=[row1, row2, row3, row4], update_cols=['ground_speed'])

        row5 = {'name': 'FLRDD0815', 'receiver_name': 'Koenigsdf', 'timestamp': '2019-01-26 11:51:00', 'ground_speed': 2}
        row6 = {'name': 'FLRDD0815', 'receiver_name': 'Koenigsdf', 'timestamp': '2019-01-26 11:52:00', 'ground_speed': 3}
        row7 = {'name': 'FLRDD0815', 'receiver_name': 'Koenigsdf', 'timestamp': '2019-01-26 11:53:00', 'ground_speed': None}
        row8 = {'name': 'FLRDD0815', 'receiver_name': 'Koenigsdf', 'timestamp': '2019-01-26 11:54:00', 'ground_speed': None}

        upsert(session=session, model=AircraftBeacon, rows=[row5, row6, row7, row8], update_cols=['ground_speed'])

        result = session.query(AircraftBeacon).order_by(AircraftBeacon.timestamp).all()
        self.assertEqual(result[0].ground_speed, 2)
        self.assertEqual(result[1].ground_speed, 3)
        self.assertEqual(result[2].ground_speed, 1)
        self.assertEqual(result[3].ground_speed, None)


if __name__ == '__main__':
    unittest.main()
