import unittest
import os

from flask import current_app
from app.model import SenderInfo
from app.commands.database import import_ddb

from tests.base import TestBaseDB, db


class TestDatabase(TestBaseDB):
    def test_import_ddb(self):
        runner = current_app.test_cli_runner()
        ddb_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../custom_ddb.txt"))
        result = runner.invoke(import_ddb, ['--path', ddb_path])
        self.assertEqual(result.exit_code, 0)

        sender_infos = db.session.query(SenderInfo).all()
        self.assertEqual(len(sender_infos), 6)


if __name__ == "__main__":
    unittest.main()
