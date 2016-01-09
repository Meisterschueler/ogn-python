import unittest

from datetime import datetime

from ogn.aprs_utils import ms2fpm
from ogn.model import Beacon, AircraftBeacon
from ogn.exceptions import OgnParseError


class TestStringMethods(unittest.TestCase):
    def test_fail_validation(self):
        aircraft_beacon = AircraftBeacon()
        with self.assertRaises(OgnParseError):
            aircraft_beacon.parse("notAValidToken")

    def test_basic(self):
        aircraft_beacon = AircraftBeacon()
        aircraft_beacon.parse("id0ADDA5BA -454fpm -1.1rot 8.8dB 0e +51.2kHz gps4x5 hear1084 hearB597 hearB598")

        self.assertFalse(aircraft_beacon.stealth)
        self.assertEqual(aircraft_beacon.address, "DDA5BA")
        self.assertAlmostEqual(aircraft_beacon.climb_rate * ms2fpm, -454, 2)
        self.assertEqual(aircraft_beacon.turn_rate, -1.1)
        self.assertEqual(aircraft_beacon.signal_strength, 8.8)
        self.assertEqual(aircraft_beacon.error_count, 0)
        self.assertEqual(aircraft_beacon.frequency_offset, 51.2)
        self.assertEqual(aircraft_beacon.gps_status, '4x5')

        self.assertEqual(len(aircraft_beacon.heared_aircraft_addresses), 3)
        self.assertEqual(aircraft_beacon.heared_aircraft_addresses[0], '1084')
        self.assertEqual(aircraft_beacon.heared_aircraft_addresses[1], 'B597')
        self.assertEqual(aircraft_beacon.heared_aircraft_addresses[2], 'B598')

    def test_stealth(self):
        aircraft_beacon = AircraftBeacon()
        aircraft_beacon.parse("id0ADD1234")
        self.assertFalse(aircraft_beacon.stealth)

        aircraft_beacon.parse("id8ADD1234")
        self.assertTrue(aircraft_beacon.stealth)

    def test_v024(self):
        aircraft_beacon = AircraftBeacon()
        aircraft_beacon.parse("!W26! id21400EA9 -2454fpm +0.9rot 19.5dB 0e -6.6kHz gps1x1 s6.02 h44 rDF0C56")

        self.assertEqual(aircraft_beacon.latitude, 2 / 1000 / 60)
        self.assertEqual(aircraft_beacon.longitude, 6 / 1000 / 60)
        self.assertEqual(aircraft_beacon.software_version, 6.02)
        self.assertEqual(aircraft_beacon.hardware_version, 44)
        self.assertEqual(aircraft_beacon.real_address, "DF0C56")

    def test_v024_ogn_tracker(self):
        aircraft_beacon = AircraftBeacon()
        aircraft_beacon.parse("!W34! id07353800 +020fpm -14.0rot FL004.43 38.5dB 0e -2.9kHz")

        self.assertEqual(aircraft_beacon.flightlevel, 4.43)

    def test_copy_constructor(self):
        beacon = Beacon()
        beacon.parse("FLRDDA5BA>APRS,qAS,LFMX:/160829h4415.41N/00600.03E'342/049/A=005524 id0ADDA5BA -454fpm -1.1rot 8.8dB 0e +51.2kHz gps4x5",
                     reference_date=datetime(2015, 1, 1, 16, 8, 29))
        aircraft_beacon = AircraftBeacon(beacon)

        self.assertEqual(aircraft_beacon.name, 'FLRDDA5BA')
        self.assertEqual(aircraft_beacon.address, 'DDA5BA')


if __name__ == '__main__':
    unittest.main()
