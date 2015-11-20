import unittest

from ogn.utils import get_ddb, get_country_code, wgs84_to_sphere
from ogn.model import AddressOrigin


class TestStringMethods(unittest.TestCase):
    def test_get_devices(self):
        devices = get_ddb()
        self.assertGreater(len(devices), 1000)

    def test_get_ddb_from_file(self):
        devices = get_ddb('tests/custom_ddb.txt')
        self.assertEqual(len(devices), 3)
        device = devices[0]

        self.assertEqual(device.address, 'DD4711')
        self.assertEqual(device.aircraft, 'HK36 TTC')
        self.assertEqual(device.registration, 'D-EULE')
        self.assertEqual(device.competition, 'CU')
        self.assertTrue(device.tracked)
        self.assertTrue(device.identified)

        self.assertEqual(device.address_origin, AddressOrigin.userdefined)

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
        # receiver
        lat1 = 48.865
        lon1 = 9.2225
        alt1 = 574

        # aircraft beacon
        lat2 = 48.74435
        lon2 = 9.578
        alt2 = 929

        [radius, theta, phi] = wgs84_to_sphere(lat1, lat2, lon1, lon2, alt1, alt2)
        self.assertAlmostEqual(radius, 29265.6035812215, 5)
        self.assertAlmostEqual(theta, 0.694979846308314, 5)
        self.assertAlmostEqual(phi, 117.1275408121, 5)
