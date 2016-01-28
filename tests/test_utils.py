import unittest

from ogn.utils import get_ddb, get_trackable, get_country_code, wgs84_to_sphere
from ogn.model import AddressOrigin, Beacon


class TestStringMethods(unittest.TestCase):
    def test_get_devices(self):
        devices = get_ddb()
        self.assertGreater(len(devices), 1000)

    def test_get_ddb_from_file(self):
        devices = get_ddb('tests/custom_ddb.txt')
        self.assertEqual(len(devices), 6)
        device = devices[0]

        self.assertEqual(device.address, 'DD4711')
        self.assertEqual(device.aircraft, 'HK36 TTC')
        self.assertEqual(device.registration, 'D-EULE')
        self.assertEqual(device.competition, 'CU')
        self.assertTrue(device.tracked)
        self.assertTrue(device.identified)

        self.assertEqual(device.address_origin, AddressOrigin.user_defined)

    def test_get_trackable(self):
        devices = get_ddb('tests/custom_ddb.txt')
        trackable = get_trackable(devices)
        self.assertEqual(len(trackable), 4)
        self.assertIn('FLRDD4711', trackable)
        self.assertIn('FLRDD0815', trackable)
        self.assertIn('OGNDEADBE', trackable)
        self.assertIn('ICA999999', trackable)

    def test_get_country_code(self):
        latitude = 48.0
        longitude = 11.0
        country_code = get_country_code(latitude, longitude)
        self.assertEquals(country_code, 'de')

    def test_get_country_code_bad(self):
        latitude = 0.0002274
        longitude = -0.0009119
        country_code = get_country_code(latitude, longitude)
        self.assertEqual(country_code, None)

    def test_wgs84_to_sphere(self):
        receiver_beacon = Beacon()
        receiver_beacon.latitude = 0
        receiver_beacon.longitude = 0
        receiver_beacon.altitude = 0

        # delta: one latitude degree
        aircraft_beacon = Beacon()
        aircraft_beacon.latitude = -1
        aircraft_beacon.longitude = 0
        aircraft_beacon.altitude = 0
        [radius, theta, phi] = wgs84_to_sphere(receiver_beacon, aircraft_beacon)
        self.assertAlmostEqual(radius, 60*1852, -2)
        self.assertEqual(theta, 0)
        self.assertEqual(phi, 180)

        # delta: one longitude degree at the equator
        aircraft_beacon.latitude = 0
        aircraft_beacon.longitude = -1
        aircraft_beacon.altitude = 0
        [radius, theta, phi] = wgs84_to_sphere(receiver_beacon, aircraft_beacon)
        self.assertAlmostEqual(radius, 60*1852, -2)
        self.assertEqual(theta, 0)
        self.assertEqual(phi, 90)

        # delta: 1000m altitude
        aircraft_beacon.latitude = 0
        aircraft_beacon.longitude = 0
        aircraft_beacon.altitude = 1000
        [radius, theta, phi] = wgs84_to_sphere(receiver_beacon, aircraft_beacon)
        self.assertAlmostEqual(radius, 1000, 3)
        self.assertEqual(theta, 90)
        self.assertEqual(phi, 0)

        # receiver
        receiver_beacon.latitude = 48.865
        receiver_beacon.longitude = 9.2225
        receiver_beacon.altitude = 574

        # aircraft beacon
        aircraft_beacon.latitude = 48.74435
        aircraft_beacon.longitude = 9.578
        aircraft_beacon.altitude = 929

        [radius, theta, phi] = wgs84_to_sphere(receiver_beacon, aircraft_beacon)
        self.assertAlmostEqual(radius, 29265.6035812215, -1)
        self.assertAlmostEqual(theta, 0.694979846308314, 5)
        self.assertAlmostEqual(phi, -117.1275408121, 5)
