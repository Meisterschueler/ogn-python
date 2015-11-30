import unittest
import unittest.mock as mock

from ogn.gateway.manage import run


class GatewayManagerTest(unittest.TestCase):
    # try simple user interrupt
    @mock.patch('ogn.gateway.manage.ognGateway')
    def test_run_user_interruption(self, mock_gateway):
        instance = mock_gateway.return_value
        instance.run.side_effect = KeyboardInterrupt()

        run(aprs_user="testuser")

        instance.connect.assert_called_once_with()
        self.assertEqual(instance.run.call_count, 1)
        instance.disconnect.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
