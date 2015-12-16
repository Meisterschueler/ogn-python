import unittest
import unittest.mock as mock

from datetime import datetime
from time import sleep

from ogn.aprs_parser import parse_aprs
from ogn.exceptions import AprsParseError, OgnParseError


class TestStringMethods(unittest.TestCase):
    def test_valid_beacons(self):
        with open('tests/valid_beacons.txt') as f:
            for line in f:
                parse_aprs(line, datetime(2015, 4, 10, 17, 0))

    def test_fail_none(self):
        with self.assertRaises(TypeError):
            parse_aprs(None)

    def test_fail_empty(self):
        with self.assertRaises(AprsParseError):
            parse_aprs("")

    def test_fail_bad_string(self):
        with self.assertRaises(AprsParseError):
            parse_aprs("Lachens>APRS,TCPIwontbeavalidstring")

    def test_incomplete_device_string(self):
        with self.assertRaises(OgnParseError):
            parse_aprs("ICA4B0E3A>APRS,qAS,Letzi:/072319h4711.75N\\00802.59E^327/149/A=006498 id154B0E3A -395",
                       datetime(2015, 4, 10, 7, 24))

    def test_incomplete_receiver_string(self):
        with self.assertRaises(OgnParseError):
            parse_aprs("Lachens>APRS,TCPIP*,qAC,GLIDERN2:/165334h4344.70NI00639.19E&/A=005435 v0.2.1 CPU:0.3 RAM:1764.4/21",
                       datetime(2015, 4, 10, 16, 54))

    @mock.patch('ogn.aprs_parser.Beacon')
    def test_default_reference_date(self, beacon_mock):
        instance = beacon_mock.return_value
        valid_aprs_string = "Lachens>APRS,TCPIP*,qAC,GLIDERN2:/165334h4344.70NI00639.19E&/A=005435 v0.2.1 CPU:0.3 RAM:1764.4/21"

        parse_aprs(valid_aprs_string)
        call_args = instance.parse.call_args
        sleep(1)
        parse_aprs(valid_aprs_string)
        call_args_one_second_later = instance.parse.call_args

        self.assertNotEqual(call_args, call_args_one_second_later)


if __name__ == '__main__':
    unittest.main()
