import unittest
import os

os.environ['OGN_CONFIG_MODULE'] = 'config/test.py'

from ogn_python import db   # noqa: E402


class TestBaseDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.session.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
        db.session.commit()
        db.create_all()

    def setUp(self):
        pass

    def tearDown(self):
        db.drop_all()


if __name__ == '__main__':
    unittest.main()
