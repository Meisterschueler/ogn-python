import unittest
from ogn.utils import get_ddb, get_country_code
from ogn.model.address_origin import AddressOrigin


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
        self.assertEqual(device.competition, '')
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
