import csv
import gzip
from io import StringIO
from datetime import datetime, timedelta

from flask import current_app

from aerofiles.seeyou import Reader
from ogn.parser.utils import FEETS_TO_METER
import requests

from .model import AircraftType, SenderInfoOrigin, SenderInfo, Airport, Location


DDB_URL = "http://ddb.glidernet.org/download/?t=1"
FLARMNET_URL = "http://www.flarmnet.org/files/data.fln"


address_prefixes = {"F": "FLR", "O": "OGN", "I": "ICA"}

nm2m = 1852
mi2m = 1609.34


def get_days(start, end):
    days = [start + timedelta(days=x) for x in range(0, (end - start).days + 1)]
    return days


def date_to_timestamps(date):
    start = datetime(date.year, date.month, date.day, 0, 0, 0)
    end = datetime(date.year, date.month, date.day, 23, 59, 59)
    return (start, end)


def get_ddb(csv_file=None, address_origin=SenderInfoOrigin.UNKNOWN):
    if csv_file is None:
        r = requests.get(DDB_URL)
        rows = "\n".join(i for i in r.text.splitlines() if i[0] != "#")
    else:
        r = open(csv_file, "r")
        rows = "".join(i for i in r.readlines() if i[0] != "#")

    data = csv.reader(StringIO(rows), quotechar="'", quoting=csv.QUOTE_ALL)

    sender_infos = list()
    for row in data:
        sender_info = SenderInfo()
        sender_info.address_type = row[0]
        sender_info.address = row[1]
        sender_info.aircraft = row[2]
        sender_info.registration = row[3]
        sender_info.competition = row[4]
        sender_info.tracked = row[5] == "Y"
        sender_info.identified = row[6] == "Y"
        sender_info.aircraft_type = AircraftType(int(row[7]))
        sender_info.address_origin = address_origin

        sender_infos.append(sender_info)

    return sender_infos


def get_flarmnet(fln_file=None, address_origin=SenderInfoOrigin.FLARMNET):
    if fln_file is None:
        r = requests.get(FLARMNET_URL)
        rows = [bytes.fromhex(line).decode("latin1") for line in r.text.split("\n") if len(line) == 173]
    else:
        with open(fln_file, "r") as file:
            rows = [bytes.fromhex(line.strip()).decode("latin1") for line in file.readlines() if len(line) == 173]

    sender_infos = list()
    for row in rows:
        sender_info = SenderInfo()
        sender_info.address = row[0:6].strip()
        sender_info.aircraft = row[48:69].strip()
        sender_info.registration = row[69:76].strip()
        sender_info.competition = row[76:79].strip()

        sender_infos.append(sender_info)

    return sender_infos


def get_trackable(ddb):
    result = []
    for i in ddb:
        if i.tracked and i.address_type in address_prefixes:
            result.append("{}{}".format(address_prefixes[i.address_type], i.address))
    return result


def get_airports(cupfile):
    airports = list()
    with open(cupfile) as f:
        for line in f:
            try:
                for waypoint in Reader([line]):
                    if waypoint["style"] > 5:  # reject unlandable places
                        continue

                    airport = Airport()
                    airport.name = waypoint["name"]
                    airport.code = waypoint["code"]
                    airport.country_code = waypoint["country"]
                    airport.style = waypoint["style"]
                    airport.description = waypoint["description"]
                    location = Location(waypoint["longitude"], waypoint["latitude"])
                    airport.location_wkt = location.to_wkt()
                    airport.altitude = waypoint["elevation"]["value"]
                    if waypoint["elevation"]["unit"] == "ft":
                        airport.altitude = airport.altitude * FEETS_TO_METER
                    airport.runway_direction = waypoint["runway_direction"]
                    airport.runway_length = waypoint["runway_length"]["value"]
                    if waypoint["runway_length"]["unit"] == "nm":
                        airport.altitude = airport.altitude * nm2m
                    elif waypoint["runway_length"]["unit"] == "ml":
                        airport.altitude = airport.altitude * mi2m
                    airport.frequency = waypoint["frequency"]

                    airports.append(airport)
            except AttributeError as e:
                current_app.logger.error("Failed to parse line: {} {}".format(line, e))

    return airports


def open_file(filename):
    """Opens a regular or unzipped textfile for reading."""
    f = open(filename, "rb")
    a = f.read(2)
    f.close()
    if a == b"\x1f\x8b":
        f = gzip.open(filename, "rt", encoding="latin-1")
        return f
    else:
        f = open(filename, "rt", encoding="latin-1")
        return f

def get_sql_trustworthy(source_table_alias):
    MIN_DISTANCE =   1000
    MAX_DISTANCE = 640000
    MAX_NORMALIZED_QUALITY = 40     # this is enough for > 640km
    MAX_ERROR_COUNT = 5
    MAX_CLIMB_RATE = 50

    return f"""
            ({source_table_alias}.distance IS NOT NULL AND {source_table_alias}.distance BETWEEN {MIN_DISTANCE} AND {MAX_DISTANCE})
        AND ({source_table_alias}.normalized_quality IS NOT NULL AND {source_table_alias}.normalized_quality < {MAX_NORMALIZED_QUALITY})
        AND ({source_table_alias}.error_count IS NULL OR {source_table_alias}.error_count < {MAX_ERROR_COUNT})
        AND ({source_table_alias}.climb_rate IS NULL OR {source_table_alias}.climb_rate BETWEEN -{MAX_CLIMB_RATE} AND {MAX_CLIMB_RATE})
    """