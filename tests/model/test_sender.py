import datetime

import unittest

from tests.base import TestBaseDB, db
from app.model import Sender, SenderInfo, SenderInfoOrigin


class TestStringMethods(TestBaseDB):
    def test_expiry_date(self):
        device = Sender(name="FLRDD0815", address="DD0815", software_version=6.42)

        self.assertEqual(device.expiry_date(), datetime.date(2019, 10, 31))


if __name__ == "__main__":
    unittest.main()
