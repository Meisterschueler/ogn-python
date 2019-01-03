import unittest
import os

from ogn.model import DeviceInfo
from ogn.commands.database import import_file


class TestDB(unittest.TestCase):
    session = None
    engine = None
    app = None

    def setUp(self):
        os.environ['OGN_CONFIG_MODULE'] = 'config.test'
        from ogn.commands.dbutils import engine, session
        self.session = session
        self.engine = engine

        from ogn.commands.database import init
        init()

    def tearDown(self):
        pass

    def test_import_ddb_file(self):
        session = self.session

        import_file(path=os.path.dirname(__file__) + '/../custom_ddb.txt')

        device_infos = session.query(DeviceInfo).all()
        self.assertEqual(len(device_infos), 6)


if __name__ == '__main__':
    unittest.main()
