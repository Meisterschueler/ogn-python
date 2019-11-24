import datetime
import unittest

from tests.base import TestBaseDB, db

from app.model import TakeoffLanding

from app.collect.takeoff_landings import update_entries


class TestTakeoffLanding(TestBaseDB):
    def setUp(self):
        super().setUp()

        db.session.execute("INSERT INTO airports(name, location, altitude, style) VALUES('Benediktbeuren','0101000020E6100000D5E76A2BF6C72640D4063A6DA0DB4740',609,4)")
        db.session.execute("INSERT INTO airports(name, location, altitude, style) VALUES('Koenigsdorf','0101000020E610000061E8FED7A6EE26407F20661C10EA4740',600,5)")
        db.session.execute("INSERT INTO airports(name, location, altitude, style) VALUES('Ohlstadt','0101000020E6100000057E678EBF772640A142883E32D44740',655,5)")
        db.session.execute("INSERT INTO airports(name, location, altitude, style) VALUES('Unterbuchen','0101000020E6100000462575029AF8264089F7098D4DE44740',635,3)")
        db.session.execute("UPDATE airports SET border = ST_Expand(location, 0.05)")

        db.session.execute("INSERT INTO devices(address, aircraft_type) VALUES('DDEFF7', 'GLIDER_OR_MOTOR_GLIDER')")
        db.session.execute("INSERT INTO devices(address, aircraft_type) VALUES('DDAC7C', 'GLIDER_OR_MOTOR_GLIDER')")

    def test_broken_rope(self):
        """Fill the db with a winch launch where the rope breaks. The algorithm should detect one takeoff and one landing."""

        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000009668B61829F12640330E0887F1E94740',604,'2016-07-02 10:47:12',0,0,0,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000009668B61829F12640330E0887F1E94740',605,'2016-07-02 10:47:32',0,0,-0.096520193,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000009668B61829F12640330E0887F1E94740',606,'2016-07-02 10:47:52',0,0,-0.096520193,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000009668B61829F12640330E0887F1E94740',606,'2016-07-02 10:48:12',0,0,-0.096520193,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000001B2FDD2406F12640E53C762AF3E94740',606,'2016-07-02 10:48:24',284,51.85598112,0.299720599,0.1)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000F594AFDEBBF02640623583E5F5E94740',610,'2016-07-02 10:48:26',282,88.89596764,4.729489459,-0.2)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000001C0DE02D90F026401564F188F7E94740',619,'2016-07-02 10:48:27',281,94.45196562,10.66294133,-0.3)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000ABF1D24D62F02640E12D90A0F8E94740',632,'2016-07-02 10:48:28',278,88.89596764,15.59055118,-0.7)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E610000069FD40CC38F02640C7925F2CF9E94740',650,'2016-07-02 10:48:29',273,83.33996966,18.90779782,-0.7)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000002709AF4A0FF02640C7925F2CF9E94740',670,'2016-07-02 10:48:30',272,79.63597101,20.72136144,-0.3)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000007AA85AF8E7EF2640C7925F2CF9E94740',691,'2016-07-02 10:48:31',269,79.63597101,21.02108204,-0.4)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E610000068DB43D5C2EF2640E12D90A0F8E94740',712,'2016-07-02 10:48:32',267,74.07997303,21.62560325,-0.5)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000EDA16AE19FEF2640FBC8C014F8E94740',728,'2016-07-02 10:48:33',266,68.52397506,12.36982474,-0.1)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000000AFCCE1C7FEF26401564F188F7E94740',733,'2016-07-02 10:48:34',266,68.52397506,2.21488443,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000275633585EEF26402FFF21FDF6E94740',731,'2016-07-02 10:48:35',267,68.52397506,-3.916687833,0.2)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E610000015891C3539EF26402FFF21FDF6E94740',726,'2016-07-02 10:48:36',270,74.07997303,-6.329692659,1.1)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000E63FA4DFBEEE264078C1CDCFFAE94740',712,'2016-07-02 10:48:39',280,88.89596764,-2.611125222,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000004FF9EABD0BEE2640448B6CE7FBE94740',706,'2016-07-02 10:48:43',256,90.74796697,-0.198120396,-2.5)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E610000046B921B3A0ED264003E78C28EDE94740',706,'2016-07-02 10:48:46',218,92.59996629,-0.198120396,-1.6)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E610000005C58F3177ED2640900C4C81DFE94740',703,'2016-07-02 10:48:48',202,96.30396495,-1.402082804,-1)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000211FF46C56ED26402650D7EDC6E94740',702,'2016-07-02 10:48:51',188,100.0079636,0.502921006,-1)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000806DEA295FED2640347D898BB6E94740',704,'2016-07-02 10:48:53',166,100.0079636,0.802641605,-2)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000337D898BB6ED26401383C0CAA1E94740',703,'2016-07-02 10:48:56',133,101.8599629,-1.803403607,-1.7)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000000C05593CE2ED2640FDF675E09CE94740',700,'2016-07-02 10:48:57',123,103.7119622,-2.611125222,-1.4)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000F0CCF1F778EE26409FA87F2394E94740',693,'2016-07-02 10:49:00',105,111.1199596,-2.809245618,-0.6)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000C9073D9B55EF2640BD5296218EE94740',687,'2016-07-02 10:49:04',97,112.9719589,-1.605283211,-0.1)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000006F8104C5EF26400C24287E8CE94740',682,'2016-07-02 10:49:06',97,114.8239582,-2.407924816,-0.2)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000A0648535A8F02640F597DD9387E94740',676,'2016-07-02 10:49:10',97,118.5279569,-1.402082804,0.1)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000D70FC48C03F22640621386EE7FE94740',672,'2016-07-02 10:49:16',97,116.6759575,-1.000762002,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000A72C431CEBF22640CB7F48BF7DE94740',666,'2016-07-02 10:49:20',84,114.8239582,-1.605283211,-1.5)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000BFCAA145B6F32640BD5296218EE94740',662,'2016-07-02 10:49:24',49,111.1199596,-1.203962408,-1.5)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E610000074DA40A70DF4264077E09C11A5E94740',659,'2016-07-02 10:49:27',23,107.4159609,-1.402082804,-1.4)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000009AE3EFF11CF42640347D898BB6E94740',656,'2016-07-02 10:49:29',4,101.8599629,-0.797561595,-1.8)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E610000074DA40A70DF426402650D7EDC6E94740',654,'2016-07-02 10:49:31',347,101.8599629,-1.706883414,-1)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000156A4DF38EF3264086EE7F6DEAE94740',649,'2016-07-02 10:49:36',312,98.15596427,-1.503683007,-1.4)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000FAEDEBC039F32640E53C762AF3E94740',644,'2016-07-02 10:49:38',295,96.30396495,-3.012446025,-1.2)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B04A0F30E0F22640FBC8C014F8E94740',635,'2016-07-02 10:49:40',284,94.45196562,-5.125730251,-0.7)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000F38B25BF58F22640448B6CE7FBE94740',623,'2016-07-02 10:49:43',279,92.59996629,-2.809245618,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000A5E8482EFFF12640DC1EAA16FEE94740',617,'2016-07-02 10:49:45',279,88.89596764,-3.312166624,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000009F17012859F12640F0AAF40003EA4740',607,'2016-07-02 10:49:49',279,81.48797034,-1.300482601,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000004B5658830AF12640873E323005EA4740',607,'2016-07-02 10:49:51',278,74.07997303,-0.294640589,-0.1)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000A0648535A8F0264006373FEB07EA4740',605,'2016-07-02 10:49:54',280,61.11597775,-0.096520193,0.5)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E6100000C74B378941F02640E88C28ED0DEA4740',604,'2016-07-02 10:49:58',292,48.15198247,0.101600203,0.4)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E61000001B5A643BDFEF264045DB1EAA16EA4740',604,'2016-07-02 10:50:04',302,25.92799056,0.203200406,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E610000042D2948AB3EF264074029A081BEA4740',604,'2016-07-02 10:50:10',300,5.555997978,0.101600203,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDEFF7', 'Koenigsdf', 'DDEFF7', 'GLIDER_OR_MOTOR_GLIDER','0101000020E610000013AB192CAFEF264074029A081BEA4740',603,'2016-07-02 10:50:16',0,0,-0.096520193,0)"
        )
        db.session.commit()

        # find the takeoff and the landing
        update_entries(db.session, start=datetime.datetime(2016, 7, 2, 0, 0, 0), end=datetime.datetime(2016, 7, 2, 23, 59, 59))
        takeoff_landing_query = db.session.query(TakeoffLanding).filter(db.between(TakeoffLanding.timestamp, datetime.datetime(2016, 7, 2, 0, 0, 0), datetime.datetime(2016, 7, 2, 23, 59, 59)))

        self.assertEqual(len(takeoff_landing_query.all()), 2)
        for entry in takeoff_landing_query.all():
            self.assertEqual(entry.airport.name, "Koenigsdorf")

        # we should not find the takeoff and the landing again
        update_entries(db.session, start=datetime.datetime(2016, 7, 2, 0, 0, 0), end=datetime.datetime(2016, 7, 2, 23, 59, 59))
        self.assertEqual(len(takeoff_landing_query.all()), 2)

    def test_broken_rope_with_stall(self):
        """Here we have a broken rope where the glider passes again the threshold for take off."""

        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B5040FE689EA264091FC62C92FEA4740',597,'2019-04-13 09:20:14',0,0,-0.096519999,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B5040FE689EA264091FC62C92FEA4740',595,'2019-04-13 09:20:23',0,0,-0.096519999,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B5040FE689EA264091FC62C92FEA4740',595,'2019-04-13 09:20:29',0,0,-0.096519999,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B5040FE689EA264091FC62C92FEA4740',591,'2019-04-13 09:21:01',0,0,-0.096519999,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B5040FE689EA264091FC62C92FEA4740',591,'2019-04-13 09:21:02',0,0,-0.096519999,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B5040FE689EA264091FC62C92FEA4740',589,'2019-04-13 09:21:13',0,0,-0.096519999,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B5040FE689EA264091FC62C92FEA4740',589,'2019-04-13 09:21:29',0,0,-0.096519999,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B5040FE689EA264091FC62C92FEA4740',590,'2019-04-13 09:21:48',0,0,-0.096519999,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B5040FE689EA264091FC62C92FEA4740',591,'2019-04-13 09:22:02',0,0,-0.096519999,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B5040FE689EA264091FC62C92FEA4740',592,'2019-04-13 09:22:22',0,0,0.1016,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000ED0DBE3099EA2640CA32C4B12EEA4740',593,'2019-04-13 09:22:40',102,25.925552,0.2032,0.60000002)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E610000026E4839ECDEA26401904560E2DEA4740',594,'2019-04-13 09:22:42',100,68.517532,0.2032,-0.30000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000D044D8F0F4EA2640513AB7F62BEA4740',595,'2019-04-13 09:22:43',101,81.480309,1.91008,-0.30000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E610000025396A721EEB2640A00B49532AEA4740',600,'2019-04-13 09:22:44',100,90.739433,5.6337199,-0.30000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E610000009E8B4814EEB2640CA41AA3B29EA4740',608,'2019-04-13 09:22:45',100,88.887611,9.2557602,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000087084327AEB264019133C9827EA4740',620,'2019-04-13 09:22:46',99,87.035782,12.3698,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000246416B4A3EB264052499D8026EA4740',634,'2019-04-13 09:22:47',97,83.33213,15.2908,-0.89999998)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000007958A835CDEB264067E4CDF425EA4740',650,'2019-04-13 09:22:48',94,79.628487,16.093439,-2.0999999)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000CE4C3AB7F6EB264067E4CDF425EA4740',667,'2019-04-13 09:22:49',91,75.924835,16.89608,-0.89999998)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000248613AB19EC264067E4CDF425EA4740',684,'2019-04-13 09:22:50',91,72.221184,17.20088,-0.30000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000005C532ACE3EEC264067E4CDF425EA4740',701,'2019-04-13 09:22:51',90,68.517532,16.89608,-0.30000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000003FF9C5925FEC264067E4CDF425EA4740',718,'2019-04-13 09:22:52',91,68.517532,16.19504,-0.30000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000229F615780EC264052499D8026EA4740',733,'2019-04-13 09:22:53',89,59.258408,14.28496,-1.5)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B11D82BD9CEC264052499D8026EA4740',741,'2019-04-13 09:22:54',89,57.406582,3.62204,0.30000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000789CA223B9EC264067E4CDF425EA4740',736,'2019-04-13 09:22:55',88,53.70293,-8.3413601,0.89999998)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B0AE00B9D7EC264052499D8026EA4740',724,'2019-04-13 09:22:56',89,62.962055,-14.5796,0.30000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000E97B17DCFCEC264052499D8026EA4740',710,'2019-04-13 09:22:57',92,85.18396,-12.1666,1.8)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000CC2A62EB2CED26408A7FFE6825EA4740',703,'2019-04-13 09:22:58',96,99.998558,-5.92836,2.0999999)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000936DEA295FED2640B5B55F5124EA4740',701,'2019-04-13 09:22:59',102,99.998558,0.40132001,2.4000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000CB10C7BAB8ED2640D95F764F1EEA4740',704,'2019-04-13 09:23:01',116,92.591263,2.21488,5.6999998)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000002005593CE2ED2640AE38FBF019EA4740',707,'2019-04-13 09:23:02',133,88.887611,2.8143201,7.5)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000925CFE43FAED2640E77D426313EA4740',709,'2019-04-13 09:23:03',147,88.887611,1.50876,6.9000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000CA65AD8E09EE26404BF9EABD0BEA4740',710,'2019-04-13 09:23:04',159,88.887611,0.60452002,6.9000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000003DF9EABD0BEE2640448B6CE7FBE94740',709,'2019-04-13 09:23:06',183,92.591263,-0.79755998,5.4000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000005917B7D100EE2640CBA145B6F3E94740',707,'2019-04-13 09:23:07',192,94.443085,-2.1082001,3.3)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E610000076711B0DE0ED2640A098966BE4E94740',701,'2019-04-13 09:23:09',196,99.998558,-2.61112,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000AF25E4839EED2640E08D2B1BC3E94740',695,'2019-04-13 09:23:13',202,105.55404,0.1016,1.5)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000002152DD4931ED2640AF16FEF9A3E94740',696,'2019-04-13 09:23:17',214,103.70221,-0.39624,2.4000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000EA62C92F96EC264021BF58F28BE94740',696,'2019-04-13 09:23:21',236,105.55404,0.1016,2.4000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000005CC2ABD203EC26404478557A80E94740',694,'2019-04-13 09:23:24',249,107.40586,-1.2039599,2.0999999)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000004182E2C798EB26402FEC0A907BE94740',690,'2019-04-13 09:23:26',256,111.10951,-2.2098,2.4000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000098A1F63EEEA26407DBD9CEC79E94740',685,'2019-04-13 09:23:29',268,114.81316,-1.00076,1.8)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000D1915CFE43EA2640E11A79337DE94740',684,'2019-04-13 09:23:32',277,112.96133,-0.79755998,0.89999998)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E610000044BE55C4D6E926404478557A80E94740',682,'2019-04-13 09:23:34',280,114.81316,-2.0065999,0.60000002)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E610000029ED0DBE30E92640932B1BC389E94740',675,'2019-04-13 09:23:37',292,118.51682,-1.2039599,2.4000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000D467FD40CCE826409AA87F2394E94740',675,'2019-04-13 09:23:39',307,114.81316,0.80264002,4.1999998)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000D49AE61DA7E826404BC8073D9BE94740',677,'2019-04-13 09:23:40',316,112.96133,2.0116799,5.4000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000009CC420B072E826403D9B559FABE94740',680,'2019-04-13 09:23:42',339,103.70221,1.0058399,5.4000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000002A762AF369E8264019D3728DBCE94740',681,'2019-04-13 09:23:44',358,96.294907,0.2032,4.1999998)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000F1F44A5986E82640992A1895D4E94740',679,'2019-04-13 09:23:47',10,94.443085,-2.2098,0.89999998)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000007F2E244DA9E826401982BD9CECE94740',671,'2019-04-13 09:23:50',14,96.294907,-2.2098,0.60000002)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000D3EFCCF1F7E8264099ACB00615EA4740',662,'2019-04-13 09:23:55',21,103.70221,-2.7127199,1.2)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E610000028B1759646E92640513AB7F62BEA4740',655,'2019-04-13 09:23:58',40,103.70221,-1.905,4.1999998)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000009A99999999E9264059B71B5736EA4740',652,'2019-04-13 09:24:00',60,99.998558,-1.2039599,5.0999999)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000448B6CE7FBE9264091DE96B53AEA4740',649,'2019-04-13 09:24:02',78,98.146736,-2.5095201,4.1999998)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000000AA4BA9362EA264091DE96B53AEA4740',643,'2019-04-13 09:24:04',93,98.146736,-2.8092401,3)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B4958DE1C4EA26402E81BA6E37EA4740',636,'2019-04-13 09:24:06',100,98.146736,-3.71856,1.2)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000005D6DC5FEB2EB2640B597933D2FEA4740',619,'2019-04-13 09:24:11',100,94.443085,-3.71856,-0.30000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000005BB1BFEC9EEC2640EEDCDAAF28EA4740',602,'2019-04-13 09:24:16',98,96.294907,-2.7127199,0.30000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000B003E78C28ED2640A01A2FDD24EA4740',598,'2019-04-13 09:24:19',98,88.887611,-0.70104003,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000009298966BE4ED26408A8EE4F21FEA4740',597,'2019-04-13 09:24:24',100,59.258408,-0.096519999,0.30000001)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E610000075C601E130EE2640EEFAA6C31DEA4740',596,'2019-04-13 09:24:28',86,25.925552,0,-4.1999998)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E610000091B1E4174BEE26408A8EE4F21FEA4740',597,'2019-04-13 09:24:31',66,14.814602,-0.096519999,-3)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000001F27563358EE26402722222222EA4740',597,'2019-04-13 09:24:38',0,0,0.1016,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000CAFFDAD453EE26402722222222EA4740',598,'2019-04-13 09:24:58',0,0,0.1016,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E6100000586C9DA551EE26402722222222EA4740',597,'2019-04-13 09:25:18',0,0,0.1016,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E610000003098A1F63EE2640EEEBC03923EA4740',596,'2019-04-13 09:25:36',54,1.8518252,0.1016,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E610000003CDF1F778EE2640A01A2FDD24EA4740',594,'2019-04-13 09:25:48',76,1.8518252,-0.096519999,0)"
        )
        db.session.execute(
            "INSERT INTO aircraft_beacons(name, receiver_name, address, aircraft_type, location, altitude, timestamp, track, ground_speed, climb_rate, turn_rate) VALUES('FLRDDAC7C','Koenigsd2','DDAC7C','GLIDER_OR_MOTOR_GLIDER','0101000020E61000001FF46C567DEE2640A01A2FDD24EA4740',593,'2019-04-13 09:25:59',0,0,-0.096519999,0)"
        )
        db.session.commit()

        # find the takeoff and the landing
        update_entries(db.session, start=datetime.datetime(2019, 4, 13, 0, 0, 0), end=datetime.datetime(2019, 4, 13, 23, 59, 59))
        takeoff_landings = db.session.query(TakeoffLanding).filter(db.between(TakeoffLanding.timestamp, datetime.datetime(2019, 4, 13, 0, 0, 0), datetime.datetime(2019, 4, 13, 23, 59, 59))).all()

        self.assertEqual(len(takeoff_landings), 2)
        for entry in takeoff_landings:
            self.assertEqual(entry.airport.name, "Koenigsdorf")


if __name__ == "__main__":
    unittest.main()
