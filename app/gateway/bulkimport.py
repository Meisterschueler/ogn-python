import os
import re
from datetime import datetime, timedelta
from io import StringIO
import gzip

from flask import current_app
from flask.cli import AppGroup
import click
from tqdm import tqdm
from mgrs import MGRS

from ogn.parser import parse, ParseError

from app.model import AircraftBeacon, ReceiverBeacon, AircraftType, Location
from app.gateway.process_tools import open_file

from app import db

user_cli = AppGroup("bulkimport")
user_cli.help = "Tools for accelerated data import."


basepath = os.path.dirname(os.path.realpath(__file__))

# define message types we want to proceed
AIRCRAFT_BEACON_TYPES = ["aprs_aircraft", "flarm", "tracker", "fanet", "lt24", "naviter", "skylines", "spider", "spot", "flymaster", "capturs"]
RECEIVER_BEACON_TYPES = ["aprs_receiver", "receiver"]

# define fields we want to proceed
AIRCRAFT_BEACON_FIELDS = [
    "location",
    "altitude",
    "name",
    "dstcall",
    "relay",
    "receiver_name",
    "timestamp",
    "track",
    "ground_speed",
    "address_type",
    "aircraft_type",
    "stealth",
    "address",
    "climb_rate",
    "turn_rate",
    "signal_quality",
    "error_count",
    "frequency_offset",
    "gps_quality_horizontal",
    "gps_quality_vertical",
    "software_version",
    "hardware_version",
    "real_address",
    "signal_power",
    "distance",
    "radial",
    "quality",
    "location_mgrs",
    "location_mgrs_short",
    "agl",
]

RECEIVER_BEACON_FIELDS = [
    "location",
    "altitude",
    "name",
    "dstcall",
    "receiver_name",
    "timestamp",
]


def initial_file_scan(file):
    """Scan file and get rowcount and first server timestamp."""

    row_count = 0
    timestamp = None

    for row in file:
        row_count += 1
        if timestamp is None and row[0] == '#':
            message = parse(row)
            if message['aprs_type'] == 'server':
                timestamp = message['timestamp']

    file.seek(0)
    return row_count, timestamp


class StringConverter:
    def __init__(self, reference_timestamp, auto_update_timestamp):
        self.reference_timestamp = reference_timestamp
        self.auto_update_timestamp = auto_update_timestamp

        self.mgrs = MGRS()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def _convert(self, raw_string):
        if raw_string.strip() == '':
            return

        try:
            message = parse(raw_string, reference_timestamp=self.reference_timestamp)
        except NotImplementedError as e:
            current_app.logger.error("No parser implemented for message: {}".format(raw_string))
            return
        except ParseError as e:
            current_app.logger.error("Parsing error with message: {}".format(raw_string))
            return
        except TypeError as e:
            current_app.logger.error("TypeError with message: {}".format(raw_string))
            return
        except Exception as e:
            current_app.logger.error("Other Exception with string: {}".format(raw_string))
            return

        if message['aprs_type'] not in ('server', 'position'):
            return

        elif message['aprs_type'] == 'server' and self.auto_update_timestamp is True:
            self.reference_timestamp = message['timestamp']
            return

        elif message['aprs_type'] == 'position':
            latitude = message["latitude"]
            longitude = message["longitude"]

            message["location"] = "SRID=4326;POINT({} {})".format(longitude, latitude)

            location_mgrs = self.mgrs.toMGRS(latitude, longitude).decode("utf-8")
            message["location_mgrs"] = location_mgrs
            message["location_mgrs_short"] = location_mgrs[0:5] + location_mgrs[5:7] + location_mgrs[10:12]

            if "aircraft_type" in message:
                message["aircraft_type"] = AircraftType(message["aircraft_type"]) if message["aircraft_type"] in AircraftType.list() else AircraftType.UNKNOWN

            if "gps_quality" in message:
                if message["gps_quality"] is not None and "horizontal" in message["gps_quality"]:
                    message["gps_quality_horizontal"] = message["gps_quality"]["horizontal"]
                    message["gps_quality_vertical"] = message["gps_quality"]["vertical"]
                del message["gps_quality"]

        return message

    def _get_aircraft_beacon_csv_string(self, message, none_character=''):
        csv_string = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13},{14},{15},{16},{17},{18},{19},{20},{21},{22},{23},{24},{25},{26},{27},{28},{29}\n".format(
            message['location'],
            int(message['altitude']) if message['altitude'] else none_character,
            message['name'],
            message['dstcall'],
            message['relay'] if 'relay' in message and message['relay'] else none_character,
            message['receiver_name'],
            message['timestamp'],
            message['track'] if 'track' in message and message['track'] else none_character,
            message['ground_speed'] if 'ground_speed' in message and message['ground_speed'] else none_character,
            message['address_type'] if 'address_type' in message and message['address_type'] else none_character,
            message['aircraft_type'].name if 'aircraft_type' in message and message['aircraft_type'] else AircraftType.UNKNOWN.name,
            message['stealth'] if 'stealth' in message and message['stealth'] else none_character,
            message['address'] if 'address' in message and message['address'] else none_character,
            message['climb_rate'] if 'climb_rate' in message and message['climb_rate'] else none_character,
            message['turn_rate'] if 'turn_rate' in message and message['turn_rate'] else none_character,
            message['signal_quality'] if 'signal_quality' in message and message['signal_quality'] else none_character,
            message['error_count'] if 'error_count' in message and message['error_count'] else none_character,
            message['frequency_offset'] if 'frequency_offset' in message and message['frequency_offset'] else none_character,
            message['gps_quality_horizontal'] if 'gps_quality_horizontal' in message and message['gps_quality_horizontal'] else none_character,
            message['gps_quality_vertical'] if 'gps_quality_vertical' in message and message['gps_quality_vertical'] else none_character,
            message['software_version'] if 'software_version' in message and message['software_version'] else none_character, #20
            message['hardware_version'] if 'hardware_version' in message and message['hardware_version'] else none_character,
            message['real_address'] if 'real_address' in message and message['real_address'] else none_character,
            message['signal_power'] if 'signal_power' in message and message['signal_power'] else none_character,
            message['distance'] if 'distance' in message and message['distance'] else none_character,
            message['radial'] if 'radial' in message and message['radial'] else none_character,
            message['quality'] if 'quality' in message and message['quality'] else none_character,
            message['location_mgrs'],
            message['location_mgrs_short'],
            message['agl'] if 'agl' in message else none_character, #29
        )
        return csv_string

    def _get_receiver_beacon_csv_string(self, message, none_character=''):
        csv_string = "{0},{1},{2},{3},{4},{5}\n".format(
            message['location'],
            int(message['altitude']) if message['altitude'] else none_character,
            message['name'],
            message['dstcall'],
            message['receiver_name'],
            message['timestamp'],
        )
        return csv_string


class FileFeeder(StringConverter):
    def __init__(self, postfix, reference_timestamp, reference_timestamp_autoupdate):
        self.reference_timestamp = reference_timestamp
        self.reference_timestamp_autoupdate = reference_timestamp_autoupdate

        self.aircraft_beacons_file = gzip.open('aircraft_beacons_{}.csv.gz'.format(postfix), 'wt')
        self.receiver_beacons_file = gzip.open('receiver_beacons_{}.csv.gz'.format(postfix), 'wt')

        super().__init__(reference_timestamp, reference_timestamp_autoupdate)

    def __enter__(self):
        self.aircraft_beacons_file.write(','.join(AIRCRAFT_BEACON_FIELDS))
        self.receiver_beacons_file.write(','.join(RECEIVER_BEACON_FIELDS))
        return self

    def __exit__(self, *args):
        self.aircraft_beacons_file.close()
        self.receiver_beacons_file.close()

    def add(self, raw_string):
        message = self._convert(raw_string)
        if message['beacon_type'] in AIRCRAFT_BEACON_TYPES:
            csv_string = self._get_aircraft_beacon_csv_string(message)
            self.aircraft_beacons_file.write(csv_string)
        elif message['beacon_type'] in RECEIVER_BEACON_TYPES:
            csv_string = self._get_receiver_beacon_csv_string(message)
            self.receiver_beacons_file.write(csv_string)


class DbFeeder(StringConverter):
    def __init__(self, reference_timestamp, reference_timestamp_autoupdate):
        self.reference_timestamp = reference_timestamp
        self.reference_timestamp_autoupdate = reference_timestamp_autoupdate

        self.aircraft_beacons_buffer = StringIO()
        self.receiver_beacons_buffer = StringIO()

        self.last_flush = datetime.utcnow()

        super().__init__(reference_timestamp, reference_timestamp_autoupdate)

    def __exit__(self, *args):
        self.flush()

    def add(self, raw_string):
        raw_string = raw_string.strip()

        message = self._convert(raw_string)
        if not message:
            return

        if message['beacon_type'] in AIRCRAFT_BEACON_TYPES:
            csv_string = self._get_aircraft_beacon_csv_string(message, none_character=r'\N')
            self.aircraft_beacons_buffer.write(csv_string)
        elif message['beacon_type'] in RECEIVER_BEACON_TYPES:
            csv_string = self._get_receiver_beacon_csv_string(message, none_character=r'\N')
            self.receiver_beacons_buffer.write(csv_string)
        else:
            current_app.logger.error(f"Not supported beacon type, skipped: {raw_string}")

        if datetime.utcnow() - self.last_flush >= timedelta(seconds=1):
            self.flush()
            self.last_flush = datetime.utcnow()

    def flush(self):
        connection = db.engine.raw_connection()
        cursor = connection.cursor()

        self.aircraft_beacons_buffer.seek(0)
        self.receiver_beacons_buffer.seek(0)

        cursor.execute("CREATE TEMPORARY TABLE aircraft_beacons_temp (LIKE aircraft_beacons) ON COMMIT DROP;")
        cursor.execute("CREATE TEMPORARY TABLE receiver_beacons_temp (LIKE receiver_beacons) ON COMMIT DROP;")

        cursor.copy_from(file=self.aircraft_beacons_buffer, table="aircraft_beacons_temp", sep=",", columns=AIRCRAFT_BEACON_FIELDS)
        cursor.copy_from(file=self.receiver_beacons_buffer, table="receiver_beacons_temp", sep=",", columns=RECEIVER_BEACON_FIELDS)

        # Update receivers
        cursor.execute("""
            INSERT INTO receivers AS r (name, location, altitude, firstseen, lastseen, timestamp)
            SELECT DISTINCT ON (rbt.name)
                rbt.name,
                rbt.location,
                rbt.altitude,
                timezone('utc', NOW()) AS firstseen,
                timezone('utc', NOW()) AS lastseen,
                rbt.timestamp
            FROM receiver_beacons_temp AS rbt,
            (
                SELECT
                    rbt.name,
                    MAX(timestamp) AS timestamp
                FROM receiver_beacons_temp AS rbt
                GROUP BY rbt.name
            ) AS sq
            WHERE rbt.name = sq.name AND rbt.timestamp = sq.timestamp
            ON CONFLICT (name) DO UPDATE
            SET
                location = EXCLUDED.location,
                altitude = EXCLUDED.altitude,
                lastseen = timezone('utc', NOW()),
                timestamp = EXCLUDED.timestamp
        """)

        # Update agl
        cursor.execute("""
            UPDATE aircraft_beacons_temp AS abt
            SET
                agl = ST_Value(e.rast, abt.location)
            FROM elevation AS e
            WHERE ST_Intersects(abt.location, e.rast)
        """)

        # ... update receiver related attributes: distance, radial, quality 
        cursor.execute("""
            UPDATE aircraft_beacons_temp AS abt
            SET
                distance = CAST(ST_DistanceSphere(r.location, abt.location) AS REAL),
                radial = CASE WHEN Degrees(ST_Azimuth(r.location, abt.location)) >= 359.5 THEN 0 ELSE CAST(Degrees(ST_Azimuth(r.location, abt.location)) AS INT) END,
                quality = CASE WHEN ST_DistanceSphere(r.location, abt.location) > 0 THEN CAST(abt.signal_quality + 20.0 * LOG(ST_DistanceSphere(r.location, abt.location) / 10000) AS REAL) ELSE NULL END
            FROM receivers AS r
            WHERE abt.receiver_name = r.name
        """)

        # Insert all the beacons
        cursor.execute("""
            INSERT INTO aircraft_beacons
            SELECT * FROM aircraft_beacons_temp
            ON CONFLICT DO NOTHING;
        """)
        cursor.execute("""
            INSERT INTO receiver_beacons
            SELECT * FROM receiver_beacons_temp
            ON CONFLICT DO NOTHING;
        """)
        connection.commit()

        cursor.close()
        connection.close()

        self.aircraft_beacons_buffer = StringIO()
        self.receiver_beacons_buffer = StringIO()


def convert(sourcefile):
    print("Fast scan of file '{}'...".format(sourcefile), end='')
    with open_file(sourcefile) as filehandler:
        total_lines, reference_timestamp = initial_file_scan(filehandler)
    print("done")

    if reference_timestamp is not None:
        auto_update_timestamp = True
        postfix = str(reference_timestamp.total_seconds())
    else:
        auto_update_timestamp = False
        match = re.match(r".*OGN_log\.txt_([0-9]{4}\-[0-9]{2}\-[0-9]{2})\.gz$", sourcefile)
        if match:
            reference_timestamp = datetime.strptime(match.group(1), "%Y-%m-%d") + timedelta(hours=12)
            postfix = reference_timestamp.strftime("%Y_%m_%d")
        else:
            current_app.logger.error("No reference time information. Skipping file: {}".format(sourcefile))
            return

    with open_file(sourcefile) as fin:
        with FileFeeder(postfix=postfix, reference_timestamp=reference_timestamp, auto_update_timestamp=auto_update_timestamp) as feeder:
            pbar = tqdm(fin, total=total_lines)
            for line in pbar:
                pbar.set_description("Importing {}".format(sourcefile))
                feeder.add(raw_string=line)


def calculate(ab_filename, rb_filename, target_filename):
    sql_string = ("""
        DROP TABLE IF EXISTS tmp_ab;
        DROP TABLE IF EXISTS tmp_rb;

        CREATE TABLE tmp_ab
        AS
        SELECT *
        FROM aircraft_beacons
        WITH NO DATA;

        CREATE TABLE tmp_rb
        AS
        SELECT *
        FROM receiver_beacons
        WITH NO DATA;

        COPY tmp_ab FROM PROGRAM 'gunzip -c {ab_filename}' CSV DELIMITER ',' HEADER;
        COPY tmp_rb FROM PROGRAM 'gunzip -c {rb_filename}' CSV DELIMITER ',' HEADER;

        COPY (
            WITH sq AS (
                SELECT
                  'SRID=4326;' || ST_AsText(ab.location) AS location,
                  ab.altitude,
                  ab.name,
                  ab.dstcall,
                  ab.relay,
                  ab.receiver_name,
                  ab.timestamp,
                  CASE WHEN ab.track = 360 THEN 0 ELSE ab.track END,
                  ab.ground_speed,
                  ab.address_type,
                  ab.aircraft_type,
                  ab.stealth,
                  ab.address,
                  ab.climb_rate,
                  ab.turn_rate,
                  ab.signal_quality,
                  ab.error_count,
                  ab.frequency_offset,
                  ab.gps_quality_horizontal,
                  ab.gps_quality_vertical,
                  ab.software_version,
                  ab.hardware_version,
                  ab.real_address,
                  ab.signal_power,
                  CAST(ST_DistanceSphere(rb.location, ab.location) AS REAL) AS distance,
                  CASE WHEN Degrees(ST_Azimuth(rb.location, ab.location)) >= 359.5 THEN 0 ELSE CAST(Degrees(ST_Azimuth(rb.location, ab.location)) AS INT) END AS radial,
                  CASE WHEN ST_DistanceSphere(rb.location, ab.location) > 0 THEN CAST(ab.signal_quality + 20.0 * LOG(ST_DistanceSphere(rb.location, ab.location) / 10000) AS REAL) ELSE NULL END quality,
                  ab.location_mgrs,
                  ab.location_mgrs_short,
                  ab.altitude - ST_Value(e.rast, ab.location) AS agl 
                FROM tmp_ab AS ab, elevation AS e, (SELECT name, MAX(location) AS location FROM tmp_rb GROUP BY name) AS rb
                WHERE ab.receiver_name = rb.name AND ST_Intersects(ab.location, e.rast)
            )

            SELECT DISTINCT ON (name, receiver_name, timestamp) *
            FROM sq
        ) TO PROGRAM 'gzip > {target_filename}' CSV DELIMITER ',' HEADER;

        COPY (
            SELECT DISTINCT ON (name, receiver_name, timestamp) *
            FROM tmp_rb AS rb
        ) TO PROGRAM 'gzip > {rb_filename}2' CSV DELIMITER ',' HEADER;
        """.format(ab_filename=ab_filename, rb_filename=rb_filename, target_filename=target_filename))

    db.session.execute(sql_string)
