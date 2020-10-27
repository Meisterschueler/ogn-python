import os
import unittest
import datetime
from app.model import AircraftBeacon, ReceiverBeacon
from app.gateway.bulkimport import DbFeeder

from tests.base import TestBaseDB, db

class TestDatabase(TestBaseDB):
    def test_valid_messages(self):
        """This test insert all valid beacons. source: https://github.com/glidernet/ogn-aprs-protocol/valid_messages"""

        path = os.path.join(os.path.dirname(__file__), 'valid_messages')
        with os.scandir(path) as it:
            for entry in it:
                if entry.name.endswith(".txt") and entry.is_file():
                    with DbFeeder() as feeder:
                        print(f"Parsing {entry.name}")
                        with open(entry.path) as file:
                            for line in file:
                                feeder.add(line, datetime.datetime(2020, 5, 1, 13, 22, 1))

    def test_ognsdr_beacons(self):
        """This test tests if status+position is correctly merged."""

        aprs_stream = (
            "LILH>OGNSDR,TCPIP*,qAC,GLIDERN2:/132201h4457.61NI00900.58E&/A=000423\n"
            "LILH>OGNSDR,TCPIP*,qAC,GLIDERN2:>132201h v0.2.7.RPI-GPU CPU:0.7 RAM:770.2/968.2MB NTP:1.8ms/-3.3ppm +55.7C 7/8Acfts[1h] RF:+54-1.1ppm/-0.16dB/+7.1dB@10km[19481]/+16.8dB@10km[7/13]"
        )

        with DbFeeder() as feeder:
            for line in aprs_stream.split('\n'):
                feeder.add(line, datetime.datetime(2020, 5, 1, 13, 22, 1))

        self.assertEqual(len(db.session.query(ReceiverBeacon).all()), 1)
        for ab in db.session.query(ReceiverBeacon).all():
            print(ab)

    def test_oneminute(self):
        with DbFeeder() as feeder:
            with open(os.path.dirname(__file__) + '/beacon_data/logs/oneminute.txt') as f:
                for line in f:
                    timestamp = datetime.datetime.strptime(line[:26], '%Y-%m-%d %H:%M:%S.%f')
                    aprs_string = line[28:]
                    feeder.add(aprs_string, reference_timestamp=timestamp)


if __name__ == "__main__":
    #unittest.main()
    if True:
        import cProfile
        
        from app import create_app
        app = create_app()
        with app.app_context():
            cProfile.run('TestDatabase().test_oneminute()', sort='tottime')
