import unittest

from ogn.model import AircraftBeacon, Airport, ReceiverBeacon


class TestStringMethods(unittest.TestCase):
    def test_string(self):
        print(AircraftBeacon())
        print(Airport())
        print(ReceiverBeacon())


if __name__ == '__main__':
    unittest.main()
