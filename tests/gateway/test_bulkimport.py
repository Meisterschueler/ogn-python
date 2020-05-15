import os
import unittest
from datetime import datetime
from app.model import AircraftBeacon, ReceiverBeacon
from app.gateway.bulkimport import DbFeeder

from tests.base import TestBaseDB, db


class TestDatabase(TestBaseDB):
    def test_valid_messages(self):
        """This test insert all valid beacons. source: https://github.com/glidernet/ogn-aprs-protocol/valid_messages"""

        path = os.path.join(os.path.dirname(__file__), 'valid_messages')
        with DbFeeder(reference_timestamp=datetime.utcnow(), reference_timestamp_autoupdate=True) as feeder:
            with os.scandir(path) as it:
                for entry in it:
                    if entry.name.endswith(".txt") and entry.is_file():
                        print(f"Parsing {entry.name}")
                        with open(entry.path) as file:
                            for line in file:
                                feeder.add(line)
                        feeder.flush()

    @unittest.skip('currently only positions are considered')
    def test_ognsdr_beacons(self):
        """This test tests if status+position is correctly merged."""

        aprs_stream = (
            "LILH>OGNSDR,TCPIP*,qAC,GLIDERN2:/132201h4457.61NI00900.58E&/A=000423\n"
            "LILH>OGNSDR,TCPIP*,qAC,GLIDERN2:>132201h v0.2.7.RPI-GPU CPU:0.7 RAM:770.2/968.2MB NTP:1.8ms/-3.3ppm +55.7C 7/8Acfts[1h] RF:+54-1.1ppm/-0.16dB/+7.1dB@10km[19481]/+16.8dB@10km[7/13]"
        )

        with DbFeeder(reference_timestamp=datetime.utcnow(), reference_timestamp_autoupdate=True) as feeder:
            for line in aprs_stream.split('\n'):
                feeder.add(line)

        self.assertEqual(len(db.session.query(ReceiverBeacon).all()), 1)
        for ab in db.session.query(ReceiverBeacon).all():
            print(ab)


if __name__ == "__main__":
    unittest.main()
