import datetime

import unittest

from tests.base import TestBaseDB, db
from app.model import Sender, SenderInfo, SenderInfoOrigin


class TestStringMethods(TestBaseDB):
    def test_sender_info(self):
        sender = Sender(name="FLRDD0815", address="DD0815")
        sender_info1 = SenderInfo(address="DD0815", address_origin=SenderInfoOrigin.OGN_DDB, registration="D-0815")
        sender_info2 = SenderInfo(address="DD0815", address_origin=SenderInfoOrigin.FLARMNET, registration="15")

        db.session.add(sender)
        db.session.add(sender_info1)
        db.session.add(sender_info2)
        db.session.commit()

        self.assertEqual(len(sender.infos), 2)
        self.assertEqual(sender.infos[0], sender_info1)

    def test_expiry_date(self):
        device = Sender(name="FLRDD0815", address="DD0815", software_version=6.42)

        self.assertEqual(device.expiry_date(), datetime.date(2019, 10, 31))


if __name__ == "__main__":
    unittest.main()
