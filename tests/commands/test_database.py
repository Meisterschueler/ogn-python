import unittest
import os

from tests.base import TestBaseDB

from ogn.model import DeviceInfo
from ogn.commands.database import import_file


class TestDatabase(TestBaseDB):
    def test_import_ddb_file(self):
        session = self.session

        import_file(path=os.path.dirname(__file__) + '/../custom_ddb.txt')

        device_infos = session.query(DeviceInfo).all()
        self.assertEqual(len(device_infos), 6)


if __name__ == '__main__':
    unittest.main()
