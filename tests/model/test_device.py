import datetime

import unittest

from tests.base import TestBaseDB, db
from ogn_python.model import Device, DeviceInfo


class TestStringMethods(TestBaseDB):
    def test_device_info(self):
        device = Device(name='FLRDD0815', address='DD0815')
        device_info1 = DeviceInfo(address='DD0815', address_origin=1, registration='D-0815')
        device_info2 = DeviceInfo(address='DD0815', address_origin=2, registration='15')

        db.session.add(device)
        db.session.add(device_info1)
        db.session.add(device_info2)
        db.session.commit()

        self.assertEqual(device.info, device_info1)

    def test_expiry_date(self):
        device = Device(name='FLRDD0815', address='DD0815', software_version=6.42)

        self.assertEqual(device.expiry_date(), datetime.date(2019, 10, 31))


if __name__ == '__main__':
    unittest.main()
