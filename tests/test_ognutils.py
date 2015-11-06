import unittest
from ogn.ognutils import get_devices_from_ddb, get_country_code


class TestStringMethods(unittest.TestCase):
    def test_get_devices_from_ddb(self):
        devices = get_devices_from_ddb()
        self.assertGreater(len(devices), 1000)

    def test_get_country_code(self):
        latitude = 48.0
        longitude = 11.0
        country_code = get_country_code(latitude, longitude)
        self.assertEquals(country_code, 'de')
