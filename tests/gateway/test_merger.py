import datetime
import unittest
from unittest.mock import MagicMock, call

from ogn.gateway.process_tools import Merger


class MergerTest(unittest.TestCase):
    def test_different_keys(self):
        a = {'name': 'Jeff', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45)}
        b = {'name': 'John', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45)}
        c = {'name': 'John', 'receiver_name': 'Observer2', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45)}
        d = {'name': 'John', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 46)}

        callback = MagicMock()
        merger = Merger(callback=callback)
        merger.add_message(a)
        callback.add_message.assert_not_called()

        merger.add_message(b)
        callback.add_message.assert_not_called()

        merger.add_message(c)
        callback.add_message.assert_not_called()

        merger.add_message(d)
        callback.add_message.assert_called_once_with(b)

        merger.flush()
        calls = [call(a), call(c), call(d)]
        callback.add_message.assert_has_calls(calls, any_order=True)

    def test_pair(self):
        a = {'name': 'Jeff', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45), 'field_a': None, 'field_b': 3.141}
        b = {'name': 'Jeff', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45), 'field_a': 'WTF', 'field_c': None, 'field_d': 1.4142}

        merged = {'name': 'Jeff', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45), 'field_a': 'WTF', 'field_b': 3.141, 'field_d': 1.4142}

        callback = MagicMock()
        merger = Merger(callback=callback)
        merger.add_message(a)
        callback.add_message.assert_not_called()

        merger.add_message(b)
        callback.add_message.assert_called_once_with(merged)

        merger.flush()
        callback.add_message.assert_called_once_with(merged)



if __name__ == '__main__':
    unittest.main()
