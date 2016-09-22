import unittest
import unittest.mock as mock

from ogn.gateway.manage import run
from ogn.gateway.manage import import_logfile

class GatewayManagerTest(unittest.TestCase):
    # try simple user interrupt
    @mock.patch('ogn.gateway.manage.AprsClient')
    def test_run_user_interruption(self, mock_aprs_client):
        instance = mock_aprs_client.return_value
        instance.run.side_effect = KeyboardInterrupt()

        run(aprs_user="testuser")

        instance.connect.assert_called_once_with()
        self.assertEqual(instance.run.call_count, 1)
        instance.disconnect.assert_called_once_with()


class GatewayManagerTest(unittest.TestCase):
    # try to import stored OGN logfile
    @mock.patch('ogn.gateway.manage.import_logfile')
    def test_run_import_logfile(self, mock_import_logfile)
        instance = mock_import_logfile.return_value

        import_logfile(ogn_logfile = "OGN_log.txt_2016-09-21")

        instance.connect.assert_called_once_with()
        self.assertEqual(instance.run.call_count, 1)
        instance.disconnect.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
