import unittest

from datetime import datetime

from ogn.parser.utils import dmsToDeg, kts2kmh, m2feet
from ogn.model import Beacon
from ogn.exceptions import AprsParseError


class TestStringMethods(unittest.TestCase):
    def test_fail_validation(self):
        beacon = Beacon()
        with self.assertRaises(AprsParseError):
            beacon.parse("notAValidString")

    def test_basic(self):
        beacon = Beacon()

        beacon.parse("FLRDDA5BA>APRS,qAS,LFMX:/160829h4415.41N/00600.03E'342/049/A=005524 this is a comment",
                     reference_date=datetime(2015, 1, 1, 16, 8, 29))
        self.assertEqual(beacon.name, "FLRDDA5BA")
        self.assertEqual(beacon.receiver_name, "LFMX")
        self.assertEqual(beacon.timestamp.strftime('%H:%M:%S'), "16:08:29")
        self.assertAlmostEqual(beacon.latitude, dmsToDeg(44.1541), 5)
        self.assertEqual(beacon.symboltable, '/')
        self.assertAlmostEqual(beacon.longitude, dmsToDeg(6.0003), 5)
        self.assertEqual(beacon.symbolcode, '\'')
        self.assertEqual(beacon.track, 342)
        self.assertEqual(beacon.ground_speed, 49 * kts2kmh)
        self.assertAlmostEqual(beacon.altitude * m2feet, 5524, 5)
        self.assertEqual(beacon.comment, "this is a comment")


if __name__ == '__main__':
    unittest.main()
