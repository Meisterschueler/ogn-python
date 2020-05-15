import unittest
from app import create_app, db


class TestBaseDB(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.session.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        db.create_all()
        db.session.commit()

        db.session.execute("CREATE TABLE IF NOT EXISTS elevation (rast raster);")
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

        db.session.execute("DROP TABLE IF EXISTS elevaion;")
        db.session.commit()

        self.app_context.pop()


if __name__ == "__main__":
    unittest.main()
