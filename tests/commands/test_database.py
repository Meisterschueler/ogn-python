import unittest
import os

from tests.base import TestBaseDB, db

from app.model import DeviceInfo
from app.commands.database import import_file

from app import app


class TestDatabase(TestBaseDB):
    def test_import_ddb_file(self):
        runner = app.test_cli_runner()
        result = runner.invoke(import_file, [os.path.dirname(__file__) + "/../custom_ddb.txt"])
        self.assertEqual(result.exit_code, 0)

        device_infos = db.session.query(DeviceInfo).all()
        self.assertEqual(len(device_infos), 6)


if __name__ == "__main__":
    unittest.main()
