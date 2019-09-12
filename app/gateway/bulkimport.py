from datetime import datetime, timedelta
from io import StringIO

from flask import current_app
from flask.cli import AppGroup
import click
from tqdm import tqdm
from mgrs import MGRS

from ogn.parser import parse, ParseError

from app.model import AircraftBeacon, ReceiverBeacon, Location
from app.utils import open_file
from app.gateway.process_tools import *

from app import db

user_cli = AppGroup("bulkimport")
user_cli.help = "Tools for accelerated data import."


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
    "receiver_id",
    "device_id",
]
RECEIVER_BEACON_FIELDS = [
    "location",
    "altitude",
    "dstcall",
    "relay",
    "version",
    "platform",
    "cpu_load",
    "free_ram",
    "total_ram",
    "ntp_error",
    "rt_crystal_correction",
    "voltage",
    "amperage",
    "cpu_temp",
    "senders_visible",
    "senders_total",
    "rec_input_noise",
    "senders_signal",
    "senders_messages",
    "good_senders_signal",
    "good_senders",
    "good_and_bad_senders",
]


myMGRS = MGRS()


def string_to_message(raw_string, reference_date):
    global receivers

    try:
        message = parse(raw_string, reference_date)
    except NotImplementedError as e:
        current_app.logger.error("No parser implemented for message: {}".format(raw_string))
        return None
    except ParseError as e:
        current_app.logger.error("Parsing error with message: {}".format(raw_string))
        return None
    except TypeError as e:
        current_app.logger.error("TypeError with message: {}".format(raw_string))
        return None
    except Exception as e:
        current_app.logger.error("Other Exception with string: {}".format(raw_string))
        return None

    # update reference receivers and distance to the receiver
    if message["aprs_type"] == "position":
        if message["beacon_type"] in AIRCRAFT_BEACON_TYPES + RECEIVER_BEACON_TYPES:
            latitude = message["latitude"]
            longitude = message["longitude"]

            location = Location(longitude, latitude)
            message["location"] = location.to_wkt()
            location_mgrs = myMGRS.toMGRS(latitude, longitude).decode("utf-8")
            message["location_mgrs"] = location_mgrs
            message["location_mgrs_short"] = location_mgrs[0:5] + location_mgrs[5:7] + location_mgrs[10:12]

        if message["beacon_type"] in AIRCRAFT_BEACON_TYPES and "gps_quality" in message:
            if message["gps_quality"] is not None and "horizontal" in message["gps_quality"]:
                message["gps_quality_horizontal"] = message["gps_quality"]["horizontal"]
                message["gps_quality_vertical"] = message["gps_quality"]["vertical"]
            del message["gps_quality"]

    # TODO: Fix python-ogn-client 0.91
    if "senders_messages" in message and message["senders_messages"] is not None:
        message["senders_messages"] = int(message["senders_messages"])
    if "good_senders" in message and message["good_senders"] is not None:
        message["good_senders"] = int(message["good_senders"])
    if "good_and_bad_senders" in message and message["good_and_bad_senders"] is not None:
        message["good_and_bad_senders"] = int(message["good_and_bad_senders"])

    return message


class ContinuousDbFeeder:
    def __init__(self,):
        self.postfix = "continuous_import"
        self.last_flush = datetime.utcnow()
        self.last_add_missing = datetime.utcnow()
        self.last_transfer = datetime.utcnow()

        self.aircraft_buffer = StringIO()
        self.receiver_buffer = StringIO()

        create_tables(self.postfix)
        create_indices(self.postfix)

    def add(self, raw_string):
        message = string_to_message(raw_string, reference_date=datetime.utcnow())

        if message is None or ("raw_message" in message and message["raw_message"][0] == "#") or "beacon_type" not in message:
            return

        if message["beacon_type"] in AIRCRAFT_BEACON_TYPES:
            complete_message = ",".join([str(message[k]) if k in message and message[k] is not None else "\\N" for k in BEACON_KEY_FIELDS + AIRCRAFT_BEACON_FIELDS])
            self.aircraft_buffer.write(complete_message)
            self.aircraft_buffer.write("\n")
        elif message["beacon_type"] in RECEIVER_BEACON_TYPES:
            complete_message = ",".join([str(message[k]) if k in message and message[k] is not None else "\\N" for k in BEACON_KEY_FIELDS + RECEIVER_BEACON_FIELDS])
            self.receiver_buffer.write(complete_message)
            self.receiver_buffer.write("\n")
        else:
            current_app.logger.error("Ignore beacon_type: {}".format(message["beacon_type"]))
            return

        if datetime.utcnow() - self.last_flush >= timedelta(seconds=20):
            self.flush()
            self.prepare()

            self.aircraft_buffer = StringIO()
            self.receiver_buffer = StringIO()

            self.last_flush = datetime.utcnow()

        if datetime.utcnow() - self.last_add_missing >= timedelta(seconds=60):
            self.add_missing()
            self.last_add_missing = datetime.utcnow()

        if datetime.utcnow() - self.last_transfer >= timedelta(seconds=30):
            self.transfer()
            self.delete_beacons()
            self.last_transfer = datetime.utcnow()

    def flush(self):
        self.aircraft_buffer.seek(0)
        self.receiver_buffer.seek(0)

        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.copy_from(self.aircraft_buffer, "aircraft_beacons_{0}".format(self.postfix), sep=",", columns=BEACON_KEY_FIELDS + AIRCRAFT_BEACON_FIELDS)
        cursor.copy_from(self.receiver_buffer, "receiver_beacons_{0}".format(self.postfix), sep=",", columns=BEACON_KEY_FIELDS + RECEIVER_BEACON_FIELDS)
        connection.commit()

        self.aircraft_buffer = StringIO()
        self.receiver_buffer = StringIO()

    def add_missing(self):
        add_missing_receivers(self.postfix)
        add_missing_devices(self.postfix)

    def prepare(self):
        # make receivers complete
        update_receiver_beacons(self.postfix)
        update_receiver_location(self.postfix)

        # make devices complete
        update_aircraft_beacons(self.postfix)

    def transfer(self):
        # tranfer beacons
        transfer_aircraft_beacons(self.postfix)
        transfer_receiver_beacons(self.postfix)

    def delete_beacons(self):
        # delete already transfered beacons
        delete_receiver_beacons(self.postfix)
        delete_aircraft_beacons(self.postfix)


class FileDbFeeder:
    def __init__(self):
        self.postfix = "continuous_import"
        self.last_flush = datetime.utcnow()

        self.aircraft_buffer = StringIO()
        self.receiver_buffer = StringIO()

        create_tables(self.postfix)
        create_indices(self.postfix)

    def add(self, raw_string):
        message = string_to_message(raw_string, reference_date=datetime.utcnow())

        if message is None or ("raw_message" in message and message["raw_message"][0] == "#") or "beacon_type" not in message:
            return

        if message["beacon_type"] in AIRCRAFT_BEACON_TYPES:
            complete_message = ",".join([str(message[k]) if k in message and message[k] is not None else "\\N" for k in BEACON_KEY_FIELDS + AIRCRAFT_BEACON_FIELDS])
            self.aircraft_buffer.write(complete_message)
            self.aircraft_buffer.write("\n")
        elif message["beacon_type"] in RECEIVER_BEACON_TYPES:
            complete_message = ",".join([str(message[k]) if k in message and message[k] is not None else "\\N" for k in BEACON_KEY_FIELDS + RECEIVER_BEACON_FIELDS])
            self.receiver_buffer.write(complete_message)
            self.receiver_buffer.write("\n")
        else:
            current_app.logger.error("Ignore beacon_type: {}".format(message["beacon_type"]))
            return

    def prepare(self):
        # make receivers complete
        add_missing_receivers(self.postfix)
        update_receiver_location(self.postfix)

        # make devices complete
        add_missing_devices(self.postfix)

        # prepare beacons for transfer
        create_indices(self.postfix)
        update_receiver_beacons_bigdata(self.postfix)
        update_aircraft_beacons_bigdata(self.postfix)


def get_aircraft_beacons_postfixes():
    """Get the postfixes from imported aircraft_beacons logs."""

    postfixes = db.session.execute(
        """
        SELECT DISTINCT(RIGHT(tablename, 8))
        FROM pg_catalog.pg_tables
        WHERE schemaname = 'public' AND tablename LIKE 'aircraft\_beacons\_20______'
        ORDER BY RIGHT(tablename, 10);
    """
    ).fetchall()

    return [postfix for postfix in postfixes]


def export_to_path(postfix):
    import os, gzip

    aircraft_beacons_file = os.path.join(path, "aircraft_beacons_{0}.csv.gz".format(postfix))
    with gzip.open(aircraft_beacons_file, "wt", encoding="utf-8") as gzip_file:
        self.cur.copy_expert("COPY ({}) TO STDOUT WITH (DELIMITER ',', FORMAT CSV, HEADER, ENCODING 'UTF-8');".format(self.get_merged_aircraft_beacons_subquery()), gzip_file)
    receiver_beacons_file = os.path.join(path, "receiver_beacons_{0}.csv.gz".format(postfix))
    with gzip.open(receiver_beacons_file, "wt") as gzip_file:
        self.cur.copy_expert("COPY ({}) TO STDOUT WITH (DELIMITER ',', FORMAT CSV, HEADER, ENCODING 'UTF-8');".format(self.get_merged_receiver_beacons_subquery()), gzip_file)


def convert(sourcefile, datestr, saver):
    from app.gateway.process import string_to_message
    from app.gateway.process_tools import AIRCRAFT_BEACON_TYPES, RECEIVER_BEACON_TYPES
    from datetime import datetime

    fin = open_file(sourcefile)

    # get total lines of the input file
    total_lines = 0
    for line in fin:
        total_lines += 1
    fin.seek(0)

    current_line = 0
    steps = 100000
    reference_date = datetime.strptime(datestr + " 12:00:00", "%Y-%m-%d %H:%M:%S")

    pbar = tqdm(fin, total=total_lines)
    for line in pbar:
        pbar.set_description("Importing {}".format(sourcefile))

        current_line += 1
        if current_line % steps == 0:
            saver.flush()

        message = string_to_message(line.strip(), reference_date=reference_date)
        if message is None:
            continue

        dictfilt = lambda x, y: dict([(i, x[i]) for i in x if i in set(y)])

        try:
            if message["beacon_type"] in AIRCRAFT_BEACON_TYPES:
                message = dictfilt(
                    message,
                    (
                        "beacon_type",
                        "aprs_type",
                        "location_wkt",
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
                        "agl",
                        "location_mgrs",
                        "location_mgrs_short",
                        "receiver_id",
                        "device_id",
                    ),
                )

                beacon = AircraftBeacon(**message)
            elif message["beacon_type"] in RECEIVER_BEACON_TYPES:
                if "rec_crystal_correction" in message:
                    del message["rec_crystal_correction"]
                    del message["rec_crystal_correction_fine"]
                beacon = ReceiverBeacon(**message)
            saver.add(beacon)
        except Exception as e:
            print(e)

    saver.flush()
    fin.close()


@user_cli.command("file_import")
@click.argument("path")
def file_import(path):
    """Import APRS logfiles into separate logfile tables."""

    import os
    import re

    # Get Filepaths and dates to import
    results = list()
    for (root, dirs, files) in os.walk(path):
        for file in sorted(files):
            match = re.match("OGN_log\.txt_([0-9]{4}\-[0-9]{2}\-[0-9]{2})\.gz$", file)
            if match:
                results.append({"filepath": os.path.join(root, file), "datestr": match.group(1)})

    with LogfileDbSaver() as saver:
        already_imported = saver.get_datestrs()

        results = list(filter(lambda x: x["datestr"] not in already_imported, results))

        pbar = tqdm(results)
        for result in pbar:
            filepath = result["filepath"]
            datestr = result["datestr"]
            pbar.set_description("Importing data for {}".format(datestr))

            saver.set_datestr(datestr)
            saver.create_tables()
            convert(filepath, datestr, saver)
            saver.add_missing_devices()
            saver.add_missing_receivers()
