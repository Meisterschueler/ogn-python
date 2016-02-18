import unittest

from ogn.model import ReceiverBeacon
from ogn.parser.exceptions import OgnParseError


class TestStringMethods(unittest.TestCase):
    def test_fail_validation(self):
        receiver_beacon = ReceiverBeacon()
        with self.assertRaises(OgnParseError):
            receiver_beacon.parse("notAValidToken")

    def test_v022(self):
        receiver_beacon = ReceiverBeacon()

        receiver_beacon.parse("v0.2.2.x86 CPU:0.5 RAM:669.9/887.7MB NTP:1.0ms/+6.2ppm +52.0C RF:+0.06dB")
        self.assertEqual(receiver_beacon.version, '0.2.2')
        self.assertEqual(receiver_beacon.platform, 'x86')
        self.assertEqual(receiver_beacon.cpu_load, 0.5)
        self.assertEqual(receiver_beacon.cpu_temp, 52.0)
        self.assertEqual(receiver_beacon.free_ram, 669.9)
        self.assertEqual(receiver_beacon.total_ram, 887.7)
        self.assertEqual(receiver_beacon.ntp_error, 1.0)
        self.assertEqual(receiver_beacon.rec_crystal_correction, 0.0)
        self.assertEqual(receiver_beacon.rec_crystal_correction_fine, 0.0)
        self.assertEqual(receiver_beacon.rec_input_noise, 0.06)

    def test_v021(self):
        receiver_beacon = ReceiverBeacon()

        receiver_beacon.parse("v0.2.1 CPU:0.8 RAM:25.6/458.9MB NTP:0.0ms/+0.0ppm +51.9C RF:+26-1.4ppm/-0.25dB")
        self.assertEqual(receiver_beacon.rec_crystal_correction, 26)
        self.assertEqual(receiver_beacon.rec_crystal_correction_fine, -1.4)
        self.assertEqual(receiver_beacon.rec_input_noise, -0.25)


if __name__ == '__main__':
    unittest.main()
