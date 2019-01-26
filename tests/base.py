import unittest
import os

os.environ['OGN_CONFIG_MODULE'] = 'config.test'


class TestCaseDB(unittest.TestCase):
    session = None
    engine = None
    app = None

    def setUp(self):
        from ogn.commands.dbutils import engine, session
        self.session = session
        self.engine = engine

        from ogn.commands.database import drop
        drop(sure='y')

        from ogn.commands.database import init
        init()

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
