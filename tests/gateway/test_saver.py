import time
import unittest
from unittest.mock import MagicMock

from ogn.gateway.process_tools import DbSaver


class DbSaverTest(unittest.TestCase):
    def test(self):
        a = "Albert"
        b = "Bertram"
        c = "Caspar"

        session = MagicMock()
        saver = DbSaver(session=session)
        saver.add_message(a)
        session.bulk_save_objects.assert_not_called()

        saver.add_message(b)
        session.bulk_save_objects.assert_not_called()

        saver.add_message(c)
        saver.flush()
        session.bulk_save_objects.assert_called_once_with([a, b, c])

    def test_timeout(self):
        a = "Xanthippe"
        b = "Yvonne"

        session = MagicMock()
        saver = DbSaver(session=session)
        saver.add_message(a)
        session.bulk_save_objects.assert_not_called()

        time.sleep(1)

        saver.add_message(b)
        session.bulk_save_objects.assert_called_once_with([a, b])


if __name__ == '__main__':
    unittest.main()
