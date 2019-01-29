import datetime
import unittest
from unittest.mock import MagicMock

from ogn.gateway.process_tools import DbSaver


class DbSaverTest(unittest.TestCase):
    def test_different_keys(self):
        a = {'name': 'Jeff', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45)}
        b = {'name': 'John', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45)}
        c = {'name': 'John', 'receiver_name': 'Observer2', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45)}
        d = {'name': 'John', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 46)}

        session = MagicMock()
        saver = DbSaver(session=session)
        saver.add_message(a)
        saver.add_message(b)
        saver.add_message(c)
        saver.add_message(d)
        session.commit.assert_not_called()

        saver.flush()
        session.commit.assert_called_once()

    def test_pair(self):
        a = {'name': 'Jeff', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45), 'field_a': None, 'field_b': 3.141}
        b = {'name': 'Jeff', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45), 'field_a': 'WTF', 'field_c': None, 'field_d': 1.4142}

        merged = {'name': 'Jeff', 'receiver_name': 'Observer1', 'timestamp': datetime.datetime(2018, 5, 20, 18, 4, 45), 'field_a': 'WTF', 'field_b': 3.141, 'field_d': 1.4142}

        session = MagicMock()
        saver = DbSaver(session=session)
        saver.add_message(a)
        session.commit.assert_not_called()

        saver.add_message(b)
        session.commit.assert_not_called()

        saver.flush()
        session.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
