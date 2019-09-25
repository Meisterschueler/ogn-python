import os
import gzip
import time
from contextlib import contextmanager

from flask import current_app
from app import db


@contextmanager
def open_file(filename):
    """Opens a regular OR gzipped textfile for reading."""

    file = open(filename, "rb")
    a = file.read(2)
    file.close()
    if a == b"\x1f\x8b":
        file = gzip.open(filename, "rt", encoding="latin-1")
    else:
        file = open(filename, "rt", encoding="latin-1")

    try:
        yield file
    finally:
        file.close()


class Timer(object):
    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        self.tstart = time.time()

    def __exit__(self, type, value, traceback):
        if self.name:
            print("[{}]".format(self.name))
        print("Elapsed: {}".format(time.time() - self.tstart))


def drop_tables(postfix):
    """Drop tables for log file import."""

    db.session.execute("""
        DROP TABLE IF EXISTS "aircraft_beacons_{postfix}";
        DROP TABLE IF EXISTS "receiver_beacons_{postfix}";
    """.format(postfix=postfix))
    db.session.commit()


def create_tables(postfix):
    """Create tables for log file import."""

    drop_tables(postfix)
    db.session.execute("""
        CREATE TABLE aircraft_beacons_{postfix} AS TABLE aircraft_beacons WITH NO DATA;
        CREATE TABLE receiver_beacons_{postfix} AS TABLE receiver_beacons WITH NO DATA;
    """.format(postfix=postfix))
    db.session.commit()


def update_aircraft_beacons_bigdata(postfix):
    """Calculates distance/radial and quality and computes the altitude above ground level.
       Due to performance reasons we use a new table instead of updating the old."""

    db.session.execute("""
        SELECT
            ab.location, ab.altitude, ab.name, ab.dstcall, ab.relay, ab.receiver_name, ab.timestamp, ab.track, ab.ground_speed,

            ab.address_type, ab.aircraft_type, ab.stealth, ab.address, ab.climb_rate, ab.turn_rate, ab.signal_quality, ab.error_count,
            ab.frequency_offset, ab.gps_quality_horizontal, ab.gps_quality_vertical, ab.software_version, ab.hardware_version, ab.real_address, ab.signal_power,

            ab.location_mgrs,
            ab.location_mgrs_short,

            CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL THEN CAST(ST_DistanceSphere(ab.location, r.location) AS REAL) ELSE NULL END AS distance,
            CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL THEN CAST(degrees(ST_Azimuth(ab.location, r.location)) AS SMALLINT) % 360 ELSE NULL END AS radial,
            CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL AND ST_DistanceSphere(ab.location, r.location) > 0 AND ab.signal_quality IS NOT NULL
                 THEN CAST(signal_quality + 20*log(ST_DistanceSphere(ab.location, r.location)/10000) AS REAL)
                 ELSE NULL
            END AS quality,
            CAST((ab.altitude - subtable.elev_m) AS REAL) AS agl
        INTO aircraft_beacons_{postfix}_temp
        FROM
            aircraft_beacons_{postfix} AS ab
                JOIN LATERAL (
                    SELECT ab.location, MAX(ST_NearestValue(e.rast, ab.location)) as elev_m
                    FROM elevation e
                    WHERE ST_Intersects(ab.location, e.rast)
                    GROUP BY ab.location
                ) AS subtable ON TRUE,
            (SELECT name, last(location, timestamp) AS location FROM receiver_beacons_{postfix} GROUP BY name) AS r
        WHERE ab.receiver_name = r.name;

        DROP TABLE IF EXISTS "aircraft_beacons_{postfix}";
        ALTER TABLE "aircraft_beacons_{postfix}_temp" RENAME TO "aircraft_beacons_{postfix}";
    """.format(postfix=postfix))


def export_to_path(postfix, path):
    connection = db.engine.raw_connection()
    cursor = connection.cursor()

    aircraft_beacons_file = os.path.join(path, "aircraft_beacons_{postfix}.csv.gz".format(postfix=postfix))
    with gzip.open(aircraft_beacons_file, "wt", encoding="utf-8") as gzip_file:
        cursor.copy_expert("COPY ({}) TO STDOUT WITH (DELIMITER ',', FORMAT CSV, HEADER, ENCODING 'UTF-8');".format("SELECT * FROM aircraft_beacons_{postfix}".format(postfix=postfix)), gzip_file)

    receiver_beacons_file = os.path.join(path, "receiver_beacons_{postfix}.csv.gz".format(postfix=postfix))
    with gzip.open(receiver_beacons_file, "wt") as gzip_file:
        cursor.copy_expert("COPY ({}) TO STDOUT WITH (DELIMITER ',', FORMAT CSV, HEADER, ENCODING 'UTF-8');".format("SELECT * FROM receiver_beacons_{postfix}".format(postfix=postfix)), gzip_file)
