import gzip
from datetime import datetime, timedelta

from flask import current_app

from aerofiles.seeyou import Reader
from ogn.parser.utils import FEETS_TO_METER

from .model import AircraftType, SenderInfoOrigin, SenderInfo, Airport, Location


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


def get_trackable(sender_info_dicts):
    result = []
    for sender_info_dict in sender_info_dicts:
        if sender_info_dict['tracked'] and sender_info_dict['address_type'] in address_prefixes:
            result.append("{}{}".format(address_prefixes[sender_info_dict['address_type']], sender_info_dict['address']))
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
    MIN_DISTANCE = 1000
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
