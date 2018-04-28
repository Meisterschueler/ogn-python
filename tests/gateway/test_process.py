import datetime
import unittest
import unittest.mock as mock

from ogn.gateway.process import process_beacon, message_to_beacon


class ProcessManagerTest(unittest.TestCase):
    @mock.patch('ogn.gateway.process.session')
    @mock.patch('ogn.gateway.process.datetime')
    def test_process_beacon(self, mock_datetime, mock_session):
        import ogn.gateway.process as gateway_process
        gateway_process.last_commit = datetime.datetime(2015, 1, 1, 10, 0, 0)
        mock_datetime.utcnow.return_value = datetime.datetime(2015, 1, 1, 10, 0, 0)

        string1 = "ICA3DD6CD>APRS,qAS,Moosburg:/195919h4820.93N/01151.39EX264/127/A=002204 !W20! id0D3DD6CD -712fpm -0.1rot 8.5dB 0e -2.1kHz gps2x2"
        string2 = "ICA3DD6CD>APRS,qAS,Moosburg:/195925h4820.90N/01151.07EX263/126/A=002139 !W74! id0D3DD6CD -712fpm +0.0rot 7.8dB 1e -2.1kHz"

        process_beacon(string1)
        mock_session.bulk_save_objects.assert_not_called()

        mock_datetime.utcnow.return_value = datetime.datetime(2015, 1, 1, 10, 0, 1)     # one second later
        process_beacon(string2)
        self.assertEqual(mock_session.bulk_save_objects.call_count, 1)

    def test_message_to_beacon_brother(self):
        string1 = "LZHL>OGNSDR,TCPIP*,qAC,GLIDERN3:/132457h4849.09NI01708.30E&/A=000528"
        string2 = "LZHL>OGNSDR,TCPIP*,qAC,GLIDERN3:>132457h v0.2.7.arm CPU:0.9 RAM:75.3/253.6MB NTP:2.0ms/-15.2ppm +0.1C 2/2Acfts[1h] RF:+77+1.7ppm/+2.34dB/+6.5dB@10km[5411]/+10.1dB@10km[3/5]"
        string3 = "BELG>OGNSDR,TCPIP*,qAC,GLIDERN3:/132507h4509.60NI00919.20E&/A=000246"
        string4 = "BELG>OGNSDR,TCPIP*,qAC,GLIDERN3:>132507h v0.2.7.RPI-GPU CPU:1.2 RAM:35.7/455.2MB NTP:2.5ms/-5.3ppm +67.0C 1/1Acfts[1h] RF:+79+8.8ppm/+4.97dB/-0.0dB@10km[299]/+4.9dB@10km[2/32]"
        string5 = "Saleve>OGNSDR,TCPIP*,qAC,GLIDERN1:/132624h4607.70NI00610.41E&/A=004198 Antenna: chinese, on a pylon, 20 meter above ground"
        string6 = "Saleve>OGNSDR,TCPIP*,qAC,GLIDERN1:>132624h v0.2.7.arm CPU:1.7 RAM:812.3/1022.5MB NTP:1.8ms/+4.5ppm 0.000V 0.000A 3/4Acfts[1h] RF:+67+2.9ppm/+4.18dB/+11.7dB@10km[5018]/+17.2dB@10km[8/16]"

        beacon = message_to_beacon(string1, reference_date=datetime.date(2015, 1, 1), wait_for_brother=True)
        self.assertIsNone(beacon)

        beacon = message_to_beacon(string2, reference_date=datetime.date(2015, 1, 1), wait_for_brother=True)
        self.assertIsNotNone(beacon)
        self.assertEqual(beacon.aprs_type, 'merged')

        beacon = message_to_beacon(string3, reference_date=datetime.date(2015, 1, 1), wait_for_brother=True)
        self.assertIsNone(beacon)

        beacon = message_to_beacon(string4, reference_date=datetime.date(2015, 1, 1), wait_for_brother=True)
        self.assertIsNotNone(beacon)
        self.assertEqual(beacon.aprs_type, 'merged')

        beacon = message_to_beacon(string5, reference_date=datetime.date(2015, 1, 1), wait_for_brother=True)
        self.assertIsNone(beacon)

        beacon = message_to_beacon(string6, reference_date=datetime.date(2015, 1, 1), wait_for_brother=True)
        self.assertIsNotNone(beacon)
        self.assertEqual(beacon.aprs_type, 'merged')

if __name__ == '__main__':
    unittest.main()
