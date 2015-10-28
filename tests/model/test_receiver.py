import unittest

from ogn.model.receiver import Receiver


class TestStringMethods(unittest.TestCase):
    def test_v022(self):
        receiver = Receiver()

        receiver.parse("v0.2.2.x86 CPU:0.5 RAM:669.9/887.7MB NTP:1.0ms/+6.2ppm +52.0C RF:+0.06dB")
        self.assertEqual(receiver.version, '0.2.2')
        self.assertEqual(receiver.platform, 'x86')
        self.assertEqual(receiver.cpu_load, 0.5)
        self.assertEqual(receiver.cpu_temp, 52.0)
        self.assertEqual(receiver.free_ram, 669.9)
        self.assertEqual(receiver.total_ram, 887.7)
        self.assertEqual(receiver.ntp_error, 1.0)
        self.assertEqual(receiver.rec_crystal_correction, 0.0)
        self.assertEqual(receiver.rec_crystal_correction_fine, 0.0)
        self.assertEqual(receiver.rec_input_noise, 0.06)

    def test_v021(self):
        receiver = Receiver()

        receiver.parse("v0.2.1 CPU:0.8 RAM:25.6/458.9MB NTP:0.0ms/+0.0ppm +51.9C RF:+26-1.4ppm/-0.25dB")
        self.assertEqual(receiver.rec_crystal_correction, 26)
        self.assertEqual(receiver.rec_crystal_correction_fine, -1.4)
        self.assertEqual(receiver.rec_input_noise, -0.25)


if __name__ == '__main__':
    unittest.main()
