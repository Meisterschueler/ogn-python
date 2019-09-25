import os
import re
from datetime import datetime, timedelta
from io import StringIO

from flask import current_app
from flask.cli import AppGroup
import click
from tqdm import tqdm
from mgrs import MGRS

from ogn.parser import parse, ParseError

from app.model import AircraftType, Location
from app.gateway.process_tools import open_file, create_tables, drop_tables, update_aircraft_beacons_bigdata

from app import db

user_cli = AppGroup("bulkimport")
user_cli.help = "Tools for accelerated data import."


basepath = os.path.dirname(os.path.realpath(__file__))

# define message types we want to proceed
AIRCRAFT_BEACON_TYPES = ["aprs_aircraft", "flarm", "tracker", "fanet", "lt24", "naviter", "skylines", "spider", "spot", "flymaster"]
RECEIVER_BEACON_TYPES = ["aprs_receiver", "receiver"]

# define fields we want to proceed
BEACON_KEY_FIELDS = ["name", "receiver_name", "timestamp"]
AIRCRAFT_BEACON_FIELDS = [
    "location",
    "altitude",
    "dstcall",
    "relay",
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
    "dstcall",
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


class DbFeeder:
    def __init__(self, postfix, reference_timestamp, auto_update_timestamp):
        self.postfix = postfix
        self.reference_timestamp = reference_timestamp
        self.auto_update_timestamp = auto_update_timestamp

        self.last_flush = datetime.utcnow()

        self.aircraft_buffer = StringIO()
        self.receiver_buffer = StringIO()

        self.connection = db.engine.raw_connection()
        self.cursor = self.connection.cursor()

        self.mgrs = MGRS()

        create_tables(self.postfix)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._flush()
        update_aircraft_beacons_bigdata(self.postfix)
        self.connection.commit()

        self.cursor.close()
        self.connection.close()

    def _flush(self):
        self.aircraft_buffer.seek(0)
        self.receiver_buffer.seek(0)

        self.cursor.copy_from(self.aircraft_buffer, "aircraft_beacons_{postfix}".format(postfix=self.postfix), sep=",", columns=BEACON_KEY_FIELDS + AIRCRAFT_BEACON_FIELDS)
        self.cursor.copy_from(self.receiver_buffer, "receiver_beacons_{postfix}".format(postfix=self.postfix), sep=",", columns=BEACON_KEY_FIELDS + RECEIVER_BEACON_FIELDS)
        self.connection.commit()

        self.aircraft_buffer = StringIO()
        self.receiver_buffer = StringIO()

    def add(self, raw_string):
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

            location = Location(longitude, latitude)
            message["location"] = location.to_wkt()

            location_mgrs = self.mgrs.toMGRS(latitude, longitude).decode("utf-8")
            message["location_mgrs"] = location_mgrs
            message["location_mgrs_short"] = location_mgrs[0:5] + location_mgrs[5:7] + location_mgrs[10:12]

            if "aircraft_type" in message:
                message["aircraft_type"] = AircraftType(message["aircraft_type"]).name if message["aircraft_type"] in AircraftType.list() else AircraftType.UNKNOWN.name

            if "gps_quality" in message:
                if message["gps_quality"] is not None and "horizontal" in message["gps_quality"]:
                    message["gps_quality_horizontal"] = message["gps_quality"]["horizontal"]
                    message["gps_quality_vertical"] = message["gps_quality"]["vertical"]
                del message["gps_quality"]

        if message["beacon_type"] in RECEIVER_BEACON_TYPES:
            complete_message = ",".join([str(message[k]) if k in message and message[k] is not None else "\\N" for k in BEACON_KEY_FIELDS + RECEIVER_BEACON_FIELDS])
            self.receiver_buffer.write(complete_message)
            self.receiver_buffer.write("\n")
        elif message["beacon_type"] in AIRCRAFT_BEACON_TYPES:
            complete_message = ",".join([str(message[k]) if k in message and message[k] is not None else "\\N" for k in BEACON_KEY_FIELDS + AIRCRAFT_BEACON_FIELDS])
            self.aircraft_buffer.write(complete_message)
            self.aircraft_buffer.write("\n")
        else:
            current_app.logger.error("Ignore beacon_type: {}".format(message["beacon_type"]))
            return

        if datetime.utcnow() - self.last_flush >= timedelta(seconds=5):
            self._flush()
            self.last_flush = datetime.utcnow()


def convert(sourcefile):
    with open_file(sourcefile) as filehandler:
        total_lines, reference_timestamp = initial_file_scan(filehandler)

    if reference_timestamp is not None:
        auto_update_timestamp = True
        postfix = str(reference_timestamp.total_seconds())
    else:
        auto_update_timestamp = False
        match = re.match(r".*OGN_log\.txt_([0-9]{4}\-[0-9]{2}\-[0-9]{2})\.gz$", sourcefile)
        if match:
            reference_timestamp = datetime.strptime(match.group(1), "%Y-%m-%d")
            postfix = reference_timestamp.strftime("%Y_%m_%d")
        else:
            current_app.logger.error("No reference time information. Skipping file: {}".format(sourcefile))
            return

    with open_file(sourcefile) as fin:
        with DbFeeder(postfix=postfix, reference_timestamp=reference_timestamp, auto_update_timestamp=auto_update_timestamp) as feeder:
            pbar = tqdm(fin, total=total_lines)
            for line in pbar:
                pbar.set_description("Importing {}".format(sourcefile))
                feeder.add(raw_string=line)
