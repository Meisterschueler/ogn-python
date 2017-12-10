import unittest
import os

from ogn.model import TakeoffLanding

from ogn.collect.takeoff_landing import update_takeoff_landing


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

        session.execute("INSERT INTO airport(name, location, altitude, style) VALUES('Benediktbeuren','0101000020E6100000D5E76A2BF6C72640D4063A6DA0DB4740',609,4)")
        session.execute("INSERT INTO airport(name, location, altitude, style) VALUES('Koenigsdorf','0101000020E610000061E8FED7A6EE26407F20661C10EA4740',600,5)")
        session.execute("INSERT INTO airport(name, location, altitude, style) VALUES('Ohlstadt','0101000020E6100000057E678EBF772640A142883E32D44740',655,5)")

        session.execute("INSERT INTO device(address) VALUES('DDEFF7')")

    def tearDown(self):
        session = self.session
        session.execute("DELETE FROM takeoff_landing")
        session.execute("DELETE FROM aircraft_beacon")
        session.execute("DELETE FROM airport")
        session.commit()
        pass

    def count_takeoff_and_landings(self):
        session = self.session
        query = session.query(TakeoffLanding)
        i = 0
        for takeoff_landing in query.all():
            i = i + 1
            print("{} {} {} {} {} {}".format(takeoff_landing.id, takeoff_landing.device_id, takeoff_landing.airport_id, takeoff_landing.timestamp, takeoff_landing.is_takeoff, takeoff_landing.track))

        return i

    def test_broken_rope(self):
        """Fill the db with a winch launch where the rope breaks. The algorithm should detect one takeoff and one landing."""
        session = self.session

        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000009668B61829F12640330E0887F1E94740',604,'2016-07-02 10:47:12',0,0,0,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000009668B61829F12640330E0887F1E94740',605,'2016-07-02 10:47:32',0,0,-0.096520193,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000009668B61829F12640330E0887F1E94740',606,'2016-07-02 10:47:52',0,0,-0.096520193,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000009668B61829F12640330E0887F1E94740',606,'2016-07-02 10:48:12',0,0,-0.096520193,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000001B2FDD2406F12640E53C762AF3E94740',606,'2016-07-02 10:48:24',284,51.85598112,0.299720599,0.1)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000F594AFDEBBF02640623583E5F5E94740',610,'2016-07-02 10:48:26',282,88.89596764,4.729489459,-0.2)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000001C0DE02D90F026401564F188F7E94740',619,'2016-07-02 10:48:27',281,94.45196562,10.66294133,-0.3)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000ABF1D24D62F02640E12D90A0F8E94740',632,'2016-07-02 10:48:28',278,88.89596764,15.59055118,-0.7)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E610000069FD40CC38F02640C7925F2CF9E94740',650,'2016-07-02 10:48:29',273,83.33996966,18.90779782,-0.7)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000002709AF4A0FF02640C7925F2CF9E94740',670,'2016-07-02 10:48:30',272,79.63597101,20.72136144,-0.3)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000007AA85AF8E7EF2640C7925F2CF9E94740',691,'2016-07-02 10:48:31',269,79.63597101,21.02108204,-0.4)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E610000068DB43D5C2EF2640E12D90A0F8E94740',712,'2016-07-02 10:48:32',267,74.07997303,21.62560325,-0.5)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000EDA16AE19FEF2640FBC8C014F8E94740',728,'2016-07-02 10:48:33',266,68.52397506,12.36982474,-0.1)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000000AFCCE1C7FEF26401564F188F7E94740',733,'2016-07-02 10:48:34',266,68.52397506,2.21488443,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000275633585EEF26402FFF21FDF6E94740',731,'2016-07-02 10:48:35',267,68.52397506,-3.916687833,0.2)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E610000015891C3539EF26402FFF21FDF6E94740',726,'2016-07-02 10:48:36',270,74.07997303,-6.329692659,1.1)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000E63FA4DFBEEE264078C1CDCFFAE94740',712,'2016-07-02 10:48:39',280,88.89596764,-2.611125222,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000004FF9EABD0BEE2640448B6CE7FBE94740',706,'2016-07-02 10:48:43',256,90.74796697,-0.198120396,-2.5)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E610000046B921B3A0ED264003E78C28EDE94740',706,'2016-07-02 10:48:46',218,92.59996629,-0.198120396,-1.6)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E610000005C58F3177ED2640900C4C81DFE94740',703,'2016-07-02 10:48:48',202,96.30396495,-1.402082804,-1)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000211FF46C56ED26402650D7EDC6E94740',702,'2016-07-02 10:48:51',188,100.0079636,0.502921006,-1)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000806DEA295FED2640347D898BB6E94740',704,'2016-07-02 10:48:53',166,100.0079636,0.802641605,-2)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000337D898BB6ED26401383C0CAA1E94740',703,'2016-07-02 10:48:56',133,101.8599629,-1.803403607,-1.7)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000000C05593CE2ED2640FDF675E09CE94740',700,'2016-07-02 10:48:57',123,103.7119622,-2.611125222,-1.4)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000F0CCF1F778EE26409FA87F2394E94740',693,'2016-07-02 10:49:00',105,111.1199596,-2.809245618,-0.6)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000C9073D9B55EF2640BD5296218EE94740',687,'2016-07-02 10:49:04',97,112.9719589,-1.605283211,-0.1)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000006F8104C5EF26400C24287E8CE94740',682,'2016-07-02 10:49:06',97,114.8239582,-2.407924816,-0.2)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000A0648535A8F02640F597DD9387E94740',676,'2016-07-02 10:49:10',97,118.5279569,-1.402082804,0.1)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000D70FC48C03F22640621386EE7FE94740',672,'2016-07-02 10:49:16',97,116.6759575,-1.000762002,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000A72C431CEBF22640CB7F48BF7DE94740',666,'2016-07-02 10:49:20',84,114.8239582,-1.605283211,-1.5)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000BFCAA145B6F32640BD5296218EE94740',662,'2016-07-02 10:49:24',49,111.1199596,-1.203962408,-1.5)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E610000074DA40A70DF4264077E09C11A5E94740',659,'2016-07-02 10:49:27',23,107.4159609,-1.402082804,-1.4)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000009AE3EFF11CF42640347D898BB6E94740',656,'2016-07-02 10:49:29',4,101.8599629,-0.797561595,-1.8)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E610000074DA40A70DF426402650D7EDC6E94740',654,'2016-07-02 10:49:31',347,101.8599629,-1.706883414,-1)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000156A4DF38EF3264086EE7F6DEAE94740',649,'2016-07-02 10:49:36',312,98.15596427,-1.503683007,-1.4)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000FAEDEBC039F32640E53C762AF3E94740',644,'2016-07-02 10:49:38',295,96.30396495,-3.012446025,-1.2)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000B04A0F30E0F22640FBC8C014F8E94740',635,'2016-07-02 10:49:40',284,94.45196562,-5.125730251,-0.7)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000F38B25BF58F22640448B6CE7FBE94740',623,'2016-07-02 10:49:43',279,92.59996629,-2.809245618,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000A5E8482EFFF12640DC1EAA16FEE94740',617,'2016-07-02 10:49:45',279,88.89596764,-3.312166624,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000009F17012859F12640F0AAF40003EA4740',607,'2016-07-02 10:49:49',279,81.48797034,-1.300482601,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000004B5658830AF12640873E323005EA4740',607,'2016-07-02 10:49:51',278,74.07997303,-0.294640589,-0.1)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000A0648535A8F0264006373FEB07EA4740',605,'2016-07-02 10:49:54',280,61.11597775,-0.096520193,0.5)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E6100000C74B378941F02640E88C28ED0DEA4740',604,'2016-07-02 10:49:58',292,48.15198247,0.101600203,0.4)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E61000001B5A643BDFEF264045DB1EAA16EA4740',604,'2016-07-02 10:50:04',302,25.92799056,0.203200406,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E610000042D2948AB3EF264074029A081BEA4740',604,'2016-07-02 10:50:10',300,5.555997978,0.101600203,0)")
        session.execute("INSERT INTO aircraft_beacon(address, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('DDEFF7','0101000020E610000013AB192CAFEF264074029A081BEA4740',603,'2016-07-02 10:50:16',0,0,-0.096520193,0)")
        session.execute("UPDATE aircraft_beacon SET device_id = d.id FROM device d WHERE d.address='DDEFF7'")
        session.commit()

        # find the takeoff and the landing
        update_takeoff_landing(session)
        self.assertEqual(self.count_takeoff_and_landings(), 2)

        # we should not find the takeoff and the landing again
        update_takeoff_landing(session)
        self.assertEqual(self.count_takeoff_and_landings(), 2)


if __name__ == '__main__':
    unittest.main()
