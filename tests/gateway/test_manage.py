import unittest
import unittest.mock as mock

from ogn.gateway.manage import run


class GatewayTest(unittest.TestCase):

    # try simple user interrupt
    @mock.patch('ogn.gateway.manage.ognGateway')
    def test_user_interruption(self, mock_gateway):
        instance = mock_gateway.return_value
        instance.run.side_effect = KeyboardInterrupt()

        run("user_1")

        instance.connect_db.assert_called_once_with()
        instance.connect.assert_called_once_with("user_1")
        instance.run.assert_called_once_with()
        instance.disconnect.assert_called_once_with()

    # make BrokenPipeErrors and a socket error (may happen) and then a user interrupt (important!)
    @mock.patch('ogn.gateway.manage.ognGateway')
    def test_BrokenPipeError(self, mock_gateway):
        instance = mock_gateway.return_value
        instance.run.side_effect = [BrokenPipeError(), BrokenPipeError(), KeyboardInterrupt()]

        run("user_2")

        instance.connect_db.assert_called_once_with()
        self.assertTrue(instance.run.call_count, 3)
        self.assertTrue(instance.disconnect.call_count, 2)  # not called if socket crashed

if __name__ == '__main__':
    unittest.main()
