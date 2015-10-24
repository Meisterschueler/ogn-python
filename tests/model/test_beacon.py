import unittest

from ogn.aprs_utils import *
from ogn.model.beacon import Beacon


class TestStringMethods(unittest.TestCase):
    def test_basic(self):
        beacon = Beacon()

        beacon.parse("FLRDDA5BA>APRS,qAS,LFMX:/160829h4415.41N/00600.03E'342/049/A=005524 this is a comment")
        self.assertEqual(beacon.name, "FLRDDA5BA")
        self.assertEqual(beacon.receiver_name, "LFMX")
        self.assertEqual(beacon.timestamp.strftime('%H:%M:%S'), "16:08:29")
        self.assertAlmostEqual(beacon.latitude, dmsToDeg(44.1541), 5)
        self.assertEqual(beacon.symboltable, '/')
        self.assertAlmostEqual(beacon.longitude, dmsToDeg(6.0003), 5)
        self.assertEqual(beacon.symbolcode, '\'')
        self.assertEqual(beacon.ground_speed, 342*kts2kmh)
        self.assertAlmostEqual(beacon.altitude*m2feet, 5524, 5)
        self.assertEqual(beacon.comment, "this is a comment")


if __name__ == '__main__':
    unittest.main()
