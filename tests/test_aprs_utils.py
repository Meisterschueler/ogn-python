import unittest
from datetime import datetime

from ogn.aprs_utils import dmsToDeg, createTimestamp


class TestStringMethods(unittest.TestCase):
    def test_dmsToDeg(self):
        dms = 50.4830
        self.assertAlmostEqual(dmsToDeg(dms), 50.805, 5)

    def test_createTimestamp_seconds_behind(self):
        timestamp = createTimestamp('235959', datetime(2015, 10, 16,  0,  0,  1))
        self.assertEqual(timestamp,           datetime(2015, 10, 15, 23, 59, 59))

    def test_createTimestamp_seconds_before(self):
        timestamp = createTimestamp('000001', datetime(2015, 10, 15, 23, 59, 59))
        self.assertEqual(timestamp,           datetime(2015, 10, 16,  0,  0,  1))

    def test_createTimestamp_big_difference(self):
        with self.assertRaises(Exception):
            createTimestamp(datetime(2015, 10, 15, 23, 59, 59), '123456')

if __name__ == '__main__':
    unittest.main()
