import unittest

from tests.base import TestCaseDB

from ogn.model import AircraftBeacon, ReceiverBeacon, Device, Receiver
from ogn.collect.database import add_missing_devices, add_missing_receivers


class TestDatabase(TestCaseDB):
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


if __name__ == '__main__':
    unittest.main()
