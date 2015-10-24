import unittest

from ogn.model.receiver import Receiver


class TestStringMethods(unittest.TestCase):
    def test_basic(self):
        receiver = Receiver()

        receiver.parse("v0.2.2 CPU:0.8 RAM:695.7/4025.5MB NTP:16000.0ms/+0.0ppm +63.0C")
        self.assertEqual(receiver.version, '0.2.2')
        self.assertEqual(receiver.cpu_load, 0.8)
        self.assertEqual(receiver.cpu_temp, 63.0)
        self.assertEqual(receiver.free_ram, 695.7)
        self.assertEqual(receiver.total_ram, 4025.5)
        self.assertEqual(receiver.ntp_error, 16000.0)
        self.assertEqual(receiver.rec_crystal_correction, 0.0)


if __name__ == '__main__':
    unittest.main()
