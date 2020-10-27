import datetime

import unittest

from tests.base import TestBaseDB, db
from app.model import Sender, SenderInfo
from app.model.device_info_origin import SenderInfoOrigin


class TestStringMethods(TestBaseDB):
    def test_device_info(self):
        device = Sender(name="FLRDD0815", address="DD0815")
        device_info1 = SenderInfo(address="DD0815", address_origin=SenderInfoOrigin.OGN_DDB, registration="D-0815")
        device_info2 = SenderInfo(address="DD0815", address_origin=SenderInfoOrigin.FLARMNET, registration="15")

        db.session.add(device)
        db.session.add(device_info1)
        db.session.add(device_info2)
        db.session.commit()

        self.assertEqual(device.info, device_info1)

    def test_expiry_date(self):
        device = Sender(name="FLRDD0815", address="DD0815", software_version=6.42)

        self.assertEqual(device.expiry_date(), datetime.date(2019, 10, 31))


if __name__ == "__main__":
    unittest.main()
