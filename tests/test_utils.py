import os
import unittest
from datetime import date

from ogn.model import AircraftType
from ogn.utils import get_days, get_ddb, get_trackable, get_airports
import unittest.mock as mock


class TestStringMethods(unittest.TestCase):
    def test_get_days(self):
        start = date(2018, 2, 27)
        end = date(2018, 3, 2)
        days = get_days(start, end)
        self.assertEqual(days, [date(2018, 2, 27), date(2018, 2, 28), date(2018, 3, 1), date(2018, 3, 2)])

    def test_get_devices(self):
        devices = get_ddb()
        self.assertGreater(len(devices), 1000)

    def test_get_ddb_from_file(self):
        devices = get_ddb(os.path.dirname(__file__) + '/custom_ddb.txt')
        self.assertEqual(len(devices), 6)
        device = devices[0]

        self.assertEqual(device.address, 'DD4711')
        self.assertEqual(device.aircraft, 'HK36 TTC')
        self.assertEqual(device.registration, 'D-EULE')
        self.assertEqual(device.competition, 'CU')
        self.assertTrue(device.tracked)
        self.assertTrue(device.identified)
        self.assertEqual(device.aircraft_type, AircraftType.glider_or_motor_glider)

    def test_get_trackable(self):
        devices = get_ddb(os.path.dirname(__file__) + '/custom_ddb.txt')
        trackable = get_trackable(devices)
        self.assertEqual(len(trackable), 4)
        self.assertIn('FLRDD4711', trackable)
        self.assertIn('FLRDD0815', trackable)
        self.assertIn('OGNDEADBE', trackable)
        self.assertIn('ICA999999', trackable)

    def test_get_airports(self):
        airports = get_airports(os.path.dirname(__file__) + '/SeeYou.cup')
        self.assertGreater(len(airports), 1000)
