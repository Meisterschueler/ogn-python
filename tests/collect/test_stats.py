import unittest
import os

from ogn.model import DeviceStats

from ogn.collect.stats import update_device_stats


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

        session.execute("INSERT INTO device(address) VALUES('DDEFF7')")
        session.execute("INSERT INTO receiver(name) VALUES('Koenigsdf')")
        session.execute("INSERT INTO receiver(name) VALUES('Ohlstadt')")

    def tearDown(self):
        session = self.session
        session.execute("DELETE FROM aircraft_beacon")
        session.execute("DELETE FROM device")

        session.execute("DELETE FROM device_stats")
        session.execute("DELETE FROM receiver_stats")

    def test_update_device_stats(self):
        session = self.session

        session.execute("INSERT INTO aircraft_beacon(address, receiver_name, altitude, timestamp) VALUES('DDEFF7','Koenigsdf',604,'2016-07-02 10:47:12')")
        session.execute("INSERT INTO aircraft_beacon(address, receiver_name, altitude, timestamp) VALUES('DDEFF7','Koenigsdf',605,'2016-07-02 10:47:32')")
        session.execute("INSERT INTO aircraft_beacon(address, receiver_name, altitude, timestamp) VALUES('DDEFF7','Koenigsdf',606,'2016-07-02 10:47:52')")
        session.execute("INSERT INTO aircraft_beacon(address, receiver_name, altitude, timestamp) VALUES('DDEFF7','Ohlstadt',606,'2016-07-02 10:48:12')")
        session.execute("INSERT INTO aircraft_beacon(address, receiver_name, altitude, timestamp) VALUES('DDEFF7','Ohlstadt',606,'2016-07-02 10:48:24')")

        session.execute("UPDATE aircraft_beacon SET device_id = d.id, receiver_id = r.id FROM device d, receiver r WHERE aircraft_beacon.address=d.address AND aircraft_beacon.receiver_name=r.name")

        update_device_stats(session, date='2016-07-02')
        stats = session.query(DeviceStats).all()

        self.assertEqual(len(stats), 1)

        stat = stats[0]
        self.assertEqual(stat.receiver_count, 2)
        self.assertEqual(stat.aircraft_beacon_count, 5)
        self.assertEqual(stat.max_altitude, 606)


if __name__ == '__main__':
    unittest.main()
