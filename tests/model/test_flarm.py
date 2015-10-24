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

        flarm.parse_flarmnet('4446304242325265696e686f6c64204dfc6c6c65722020202020204c535a46202020202020202020202020202020202056656e747573203263784d2020202020202020202048422d323532375836203132332e303030')
        self.assertEqual(flarm.address, 'DF0BB2')
        self.assertEqual(flarm.name, 'Reinhold Müller')
        self.assertEqual(flarm.airport, 'LSZF')
        self.assertEqual(flarm.aircraft, 'Ventus 2cxM')
        self.assertEqual(flarm.registration, 'HB-2527')
        self.assertEqual(flarm.competition, 'X6')
        self.assertEqual(flarm.frequency, '123.000')

        self.assertEqual(flarm.address_origin, AddressOrigin.flarmnet)


if __name__ == '__main__':
    unittest.main()
