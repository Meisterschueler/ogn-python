import unittest

from ogn.aprs_utils import ms2fpm
from ogn.model.beacon import Beacon
from ogn.model.position import Position


class TestStringMethods(unittest.TestCase):
    def test_basic(self):
        position = Position()

        position.parse("id0ADDA5BA -454fpm -1.1rot 8.8dB 0e +51.2kHz gps4x5 hear1084 hearB597 hearB598")
        self.assertFalse(position.stealth)
        self.assertEqual(position.address, "DDA5BA")
        self.assertAlmostEqual(position.climb_rate*ms2fpm, -454, 2)
        self.assertEqual(position.turn_rate, -1.1)
        self.assertEqual(position.signal_strength, 8.8)
        self.assertEqual(position.error_count, 0)
        self.assertEqual(position.frequency_offset, 51.2)
        self.assertEqual(position.gps_status, '4x5')

        self.assertEqual(len(position.heared_aircraft_IDs), 3)
        self.assertEqual(position.heared_aircraft_IDs[0], '1084')
        self.assertEqual(position.heared_aircraft_IDs[1], 'B597')
        self.assertEqual(position.heared_aircraft_IDs[2], 'B598')

    def test_stealth(self):
        position = Position()
        position.parse("id0ADD1234")
        self.assertFalse(position.stealth)

        position.parse("id8ADD1234")
        self.assertTrue(position.stealth)

    def test_ver024(self):
        position = Position()
        position.latitude = 0.0
        position.longitude = 0.0

        position.parse("!W26! id21400EA9 -2454fpm +0.9rot 19.5dB 0e -6.6kHz gps1x1 s6.02 h44 rDF0C56")
        self.assertEqual(position.latitude, 0.002)
        self.assertEqual(position.longitude, 0.006)
        self.assertEqual(position.software_version, 6.02)
        self.assertEqual(position.hardware_version, 44)
        self.assertEqual(position.real_id, "DF0C56")

    def test_copy_constructor(self):
        beacon = Beacon()
        beacon.parse("FLRDDA5BA>APRS,qAS,LFMX:/160829h4415.41N/00600.03E'342/049/A=005524 id0ADDA5BA -454fpm -1.1rot 8.8dB 0e +51.2kHz gps4x5")
        position = Position(beacon)

        self.assertEqual(position.name, 'FLRDDA5BA')
        self.assertEqual(position.address, 'DDA5BA')


if __name__ == '__main__':
    unittest.main()
