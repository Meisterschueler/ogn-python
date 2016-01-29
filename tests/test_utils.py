import unittest

from ogn.utils import get_ddb, get_trackable, get_country_code, haversine_distance
from ogn.model import AddressOrigin


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

    def test_haversine_distance(self):
        # delta: one latitude degree
        location0 = (0, 0)
        location1 = (-1, 0)

        (distance, phi) = haversine_distance(location0, location1)
        self.assertAlmostEqual(distance, 60 * 1852, -2)
        self.assertEqual(phi, 180)

        # delta: one longitude degree at the equator
        location0 = (0, 0)
        location1 = (0, -1)

        (distance, phi) = haversine_distance(location0, location1)
        self.assertAlmostEqual(distance, 60 * 1852, -2)
        self.assertEqual(phi, 90)

        # delta: 29000m
        location0 = (48.865, 9.2225)
        location1 = (48.74435, 9.578)

        (distance, phi) = haversine_distance(location0, location1)
        self.assertAlmostEqual(distance, 29265.6035812215, -1)
        self.assertAlmostEqual(phi, -117.1275408121, 5)
