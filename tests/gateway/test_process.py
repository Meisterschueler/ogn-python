import datetime
import unittest
import unittest.mock as mock

from ogn.gateway.process import process_raw_message


class ProcessManagerTest(unittest.TestCase):
    @mock.patch('ogn.gateway.process.session')
    @mock.patch('ogn.gateway.process.datetime')
    def test_process_beacon(self, mock_datetime, mock_session):
        import ogn.gateway.process as gateway_process
        gateway_process.last_commit = datetime.datetime(2015, 1, 1, 10, 0, 0)
        mock_datetime.utcnow.return_value = datetime.datetime(2015, 1, 1, 10, 0, 0)

        string1 = "ICA3DD6CD>APRS,qAS,Moosburg:/195919h4820.93N/01151.39EX264/127/A=002204 !W20! id0D3DD6CD -712fpm -0.1rot 8.5dB 0e -2.1kHz gps2x2"
        string2 = "ICA3DD6CD>APRS,qAS,Moosburg:/195925h4820.90N/01151.07EX263/126/A=002139 !W74! id0D3DD6CD -712fpm +0.0rot 7.8dB 1e -2.1kHz"

        process_raw_message(string1)
        mock_session.bulk_save_objects.assert_not_called()

        mock_datetime.utcnow.return_value = datetime.datetime(2015, 1, 1, 10, 0, 1)     # one second later
        process_raw_message(string2)
        self.assertEqual(mock_session.bulk_save_objects.call_count, 1)


if __name__ == '__main__':
    unittest.main()
