import os
import unittest
from datetime import date

from app.model import AircraftType
from app.utils import get_days, get_trackable, get_airports
from app.commands.database import read_ddb


class TestStringMethods(unittest.TestCase):
    def test_get_days(self):
        start = date(2018, 2, 27)
        end = date(2018, 3, 2)
        days = get_days(start, end)
        self.assertEqual(days, [date(2018, 2, 27), date(2018, 2, 28), date(2018, 3, 1), date(2018, 3, 2)])

    def test_get_devices(self):
        sender_infos = read_ddb()
        self.assertGreater(len(sender_infos), 1000)

    def test_get_ddb_from_file(self):
        sender_infos = read_ddb(os.path.dirname(__file__) + "/custom_ddb.txt")
        self.assertEqual(len(sender_infos), 6)
        sender_info = sender_infos[0]

        self.assertEqual(sender_info['address'], "DD4711")
        self.assertEqual(sender_info['aircraft'], "HK36 TTC")
        self.assertEqual(sender_info['registration'], "D-EULE")
        self.assertEqual(sender_info['competition'], "CU")
        self.assertTrue(sender_info['tracked'])
        self.assertTrue(sender_info['identified'])
        self.assertEqual(sender_info['aircraft_type'], AircraftType.GLIDER_OR_MOTOR_GLIDER)

    def test_get_trackable(self):
        sender_infos = read_ddb(os.path.dirname(__file__) + "/custom_ddb.txt")
        trackable = get_trackable(sender_infos)
        self.assertEqual(len(trackable), 4)
        self.assertIn("FLRDD4711", trackable)
        self.assertIn("FLRDD0815", trackable)
        self.assertIn("OGNDEADBE", trackable)
        self.assertIn("ICA999999", trackable)

    def test_get_airports(self):
        airports = get_airports(os.path.dirname(__file__) + "/SeeYou.cup")
        self.assertGreater(len(airports), 1000)
