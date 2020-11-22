import unittest
import os

from flask import current_app
from app.model import SenderInfo
from app.commands.database import import_file

from tests.base import TestBaseDB, db


class TestDatabase(TestBaseDB):
    def test_import_ddb_file(self):
        runner = current_app.test_cli_runner()
        result = runner.invoke(import_file, [os.path.dirname(__file__) + "/../custom_ddb.txt"])
        self.assertEqual(result.exit_code, 0)

        sender_infos = db.session.query(SenderInfo).all()
        self.assertEqual(len(sender_infos), 6)


if __name__ == "__main__":
    unittest.main()
