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

def export_to_path(path):
    connection = db.engine.raw_connection()
    cursor = connection.cursor()

    aircraft_beacons_file = os.path.join(path, "sender_positions.csv.gz")
    with gzip.open(aircraft_beacons_file, "wt", encoding="utf-8") as gzip_file:
        cursor.copy_expert("COPY ({}) TO STDOUT WITH (DELIMITER ',', FORMAT CSV, HEADER, ENCODING 'UTF-8');".format("SELECT * FROM sender_positions"), gzip_file)
