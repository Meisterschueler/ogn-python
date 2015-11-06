import unittest

from ogn.model.address_origin import *
from ogn.model.flarm import Flarm


class TestStringMethods(unittest.TestCase):
    def test_ddb(self):
        flarm = Flarm()

        flarm.parse_ogn("'F','DD9703','Twin Astir II','D-8203','7G','Y','N'\r\n")
        self.assertEqual(flarm.address_type, 'F')
        self.assertEqual(flarm.address, 'DD9703')
        self.assertEqual(flarm.aircraft, 'Twin Astir II')
        self.assertEqual(flarm.registration, 'D-8203')
        self.assertEqual(flarm.competition, '7G')
        self.assertTrue(flarm.tracked)
        self.assertFalse(flarm.identified)

        self.assertEqual(flarm.address_origin, AddressOrigin.ogn_ddb)

    def test_flarmnet(self):
        flarm = Flarm()

        flarm.parse_flarmnet('444431323334486972616d205965616765722020202020202020204c535a46202020202020202020202020202020202056656e747573203263784d2020202020202020202052552d343731315836203132332e343536')
        self.assertEqual(flarm.address, 'DD1234')
        self.assertEqual(flarm.name, 'Hiram Yeager')
        self.assertEqual(flarm.airport, 'LSZF')
        self.assertEqual(flarm.aircraft, 'Ventus 2cxM')
        self.assertEqual(flarm.registration, 'RU-4711')
        self.assertEqual(flarm.competition, 'X6')
        self.assertEqual(flarm.frequency, '123.456')

        self.assertEqual(flarm.address_origin, AddressOrigin.flarmnet)


if __name__ == '__main__':
    unittest.main()
