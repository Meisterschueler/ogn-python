from flask.cli import AppGroup
import click

import psycopg2
from tqdm import tqdm
from io import StringIO

from ogn_python.model import AircraftBeacon, ReceiverBeacon
from ogn_python.utils import open_file
from ogn_python.commands.database import get_database_days

from ogn_python import db

user_cli = AppGroup('bulkimport')
user_cli.help = "Tools for accelerated data import."


ALEMBIC_CONFIG_FILE = "alembic.ini"


class LogfileDbSaver():
    def __init__(self):
        """Establish the database connection."""
        try:
            self.conn = psycopg2.connect(database="ogn", user="postgres", password="postgres", host="localhost", port="5432")
        except Exception as e:
            raise Exception("I am unable to connect to the database")
        self.cur = self.conn.cursor()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        """Closes the database connection."""

        self.cur.close()
        self.conn.close()

    def set_datestr(self, datestr):
        """Sets the datestr of the current tables."""

        self.prefix = datestr.replace('-', '_')
        self.aircraft_table = 'aircraft_beacons_{}'.format(self.prefix)
        self.receiver_table = 'receiver_beacons_{}'.format(self.prefix)
        self.aircraft_buffer = StringIO()
        self.receiver_buffer = StringIO()

    def get_datestrs(self, no_index_only=False):
        """Get the date strings from imported log files."""

        index_clause = " AND hasindexes = FALSE" if no_index_only else ""

        self.cur.execute(("""
            SELECT DISTINCT(RIGHT(tablename, 10))
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public' AND tablename LIKE 'aircraft_beacons_%'{}
            ORDER BY RIGHT(tablename, 10);
        """.format(index_clause)))

        return [datestr[0].replace('_', '-') for datestr in self.cur.fetchall()]

    def create_tables(self):
        """Create date dependent tables for log file import."""

        try:
            self.cur.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
            self.cur.execute('CREATE EXTENSION IF NOT EXISTS btree_gist;')
            self.cur.execute('DROP TABLE IF EXISTS "{0}"; CREATE TABLE {0} AS TABLE aircraft_beacons WITH NO DATA;'.format(self.aircraft_table))
            self.cur.execute('DROP TABLE IF EXISTS "{0}"; CREATE TABLE {0} AS TABLE receiver_beacons WITH NO DATA;'.format(self.receiver_table))
            self.conn.commit()
        except Exception as e:
            raise Exception("I can't create the tables")

    def add(self, beacon):
        """Adds the values of the beacon to the buffer."""

        value_string = ','.join([str(value) for value in beacon.get_values()]) + '\n'
        if isinstance(beacon, AircraftBeacon):
            self.aircraft_buffer.write(value_string)
        elif isinstance(beacon, ReceiverBeacon):
            self.receiver_buffer.write(value_string)

    def flush(self):
        """Writes the buffer into the tables and reset the buffer."""

        self.aircraft_buffer.seek(0)
        self.receiver_buffer.seek(0)
        self.cur.copy_from(self.aircraft_buffer, self.aircraft_table, sep=',', null='None', columns=AircraftBeacon.get_columns())
        self.cur.copy_from(self.receiver_buffer, self.receiver_table, sep=',', null='None', columns=ReceiverBeacon.get_columns())
        self.conn.commit()
        self.aircraft_buffer = StringIO()
        self.receiver_buffer = StringIO()

    def export_to_path(self, path):
        import os, gzip
        aircraft_beacons_file = os.path.join(path, self.aircraft_table + '.csv.gz')
        with gzip.open(aircraft_beacons_file, 'wt', encoding='utf-8') as gzip_file:
            self.cur.copy_expert("COPY ({}) TO STDOUT WITH (DELIMITER ',', FORMAT CSV, HEADER, ENCODING 'UTF-8');".format(self.get_merged_aircraft_beacons_subquery()), gzip_file)
        receiver_beacons_file = os.path.join(path, self.receiver_table + '.csv.gz')
        with gzip.open(receiver_beacons_file, 'wt') as gzip_file:
            self.cur.copy_expert("COPY ({}) TO STDOUT WITH (DELIMITER ',', FORMAT CSV, HEADER, ENCODING 'UTF-8');".format(self.get_merged_receiver_beacons_subquery()), gzip_file)

    def create_indices(self):
        """Creates indices for aircraft- and receiver-beacons."""

        self.cur.execute("""
            CREATE INDEX IF NOT EXISTS ix_{0}_timestamp_name_receiver_name ON "{0}" (timestamp, name, receiver_name);
            CREATE INDEX IF NOT EXISTS ix_{0}_device_id_timestamp_error_count ON "{0}" (device_id, timestamp, error_count);
            CREATE INDEX IF NOT EXISTS ix_{1}_timestamp_name_receiver_name ON "{1}" (timestamp, name, receiver_name);
        """.format(self.aircraft_table, self.receiver_table))
        self.conn.commit()

    def add_missing_devices(self):
        """Add missing devices."""

        self.cur.execute("""
            INSERT INTO devices(address)
            SELECT DISTINCT(ab.address)
            FROM "{}" AS ab
            WHERE NOT EXISTS (SELECT 1 FROM devices AS d WHERE d.address = ab.address)
            ORDER BY ab.address;
        """.format(self.aircraft_table))
        self.conn.commit()

    def add_missing_receivers(self):
        """Add missing receivers."""

        self.cur.execute("""
            INSERT INTO receivers(name)
            SELECT DISTINCT(rb.name)
            FROM "{0}" AS rb
            WHERE NOT EXISTS (SELECT 1 FROM receivers AS r WHERE r.name = rb.name)
            ORDER BY name;
        """.format(self.receiver_table))
        self.conn.commit()

    def update_receiver_location(self):
        """Updates the receiver location. We need this because we want the actual location for distance calculations."""

        self.cur.execute("""
            UPDATE receivers AS r
            SET location = sq.location,
            altitude = sq.altitude
            FROM
                (SELECT DISTINCT ON (rb.receiver_id) rb.receiver_id, rb.location, rb.altitude
                FROM "{1}" AS rb
                WHERE rb.location IS NOT NULL
                ORDER BY rb.receiver_id, rb.timestamp
                ) AS sq
            WHERE r.id = sq.receiver_id;
        """.format(self.aircraft_table, self.receiver_table))
        self.conn.commit()

    def update_receiver_beacons(self):
        """Updates the foreign keys. Due to performance reasons we use a new table instead of updating the old."""

        self.cur.execute("""
            SELECT

            rb.location, rb.altitude, rb.name, rb.receiver_name, rb.dstcall, rb.timestamp,

            rb.version, rb.platform, rb.cpu_load, rb.free_ram, rb.total_ram, rb.ntp_error, rb.rt_crystal_correction, rb.voltage, rb.amperage real,
            rb.cpu_temp, rb.senders_visible, rb.senders_total, rb.rec_input_noise, rb.senders_signal, rb.senders_messages, rb.good_senders_signal real,
            rb.good_senders, rb.good_and_bad_senders,

            r.id AS receiver_id
            INTO "{0}_temp"
            FROM "{0}" AS rb, receivers AS r
            WHERE rb.name = r.name;

            DROP TABLE IF EXISTS "{0}";
            ALTER TABLE "{0}_temp" RENAME TO "{0}";
        """.format(self.receiver_table))
        self.conn.commit()

    def update_aircraft_beacons(self):
        """Updates the foreign keys and calculates distance/radial and quality and computes the altitude above ground level.
           Elevation data has to be in the table 'elevation' with srid 4326.
           Due to performance reasons we use a new table instead of updating the old."""

        self.cur.execute("""
            SELECT
            ab.location, ab.altitude, ab.name, ab.dstcall, ab.relay, ab.receiver_name, ab.timestamp, ab.track, ab.ground_speed,

            ab.address_type, ab.aircraft_type, ab.stealth, ab.address, ab.climb_rate, ab.turn_rate, ab.signal_quality, ab.error_count,
            ab.frequency_offset, ab.gps_quality_horizontal, ab.gps_quality_vertical, ab.software_version, ab.hardware_version, ab.real_address, ab.signal_power,

            ab.location_mgrs,
            ab.location_mgrs_short,

            d.id AS device_id,
            r.id AS receiver_id,
            CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL THEN CAST(ST_DistanceSphere(ab.location, r.location) AS REAL) ELSE NULL END AS distance,
            CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL THEN CAST(degrees(ST_Azimuth(ab.location, r.location)) AS SMALLINT) ELSE NULL END AS radial,
            CASE WHEN ab.location IS NOT NULL AND r.location IS NOT NULL AND ST_DistanceSphere(ab.location, r.location) > 0 AND ab.signal_quality IS NOT NULL
                 THEN CAST(signal_quality + 20*log(ST_DistanceSphere(ab.location, r.location)/10000) AS REAL)
                 ELSE NULL
            END AS quality,
            CAST(ab.altitude - ST_Value(e.rast, ab.location) AS REAL) AS agl

            INTO "{0}_temp"
            FROM "{0}" AS ab, devices AS d, receivers AS r, elevation AS e
            WHERE ab.address = d.address AND receiver_name = r.name AND ST_Intersects(e.rast, ab.location);

            DROP TABLE IF EXISTS "{0}";
            ALTER TABLE "{0}_temp" RENAME TO "{0}";
        """.format(self.aircraft_table))
        self.conn.commit()

    def get_merged_aircraft_beacons_subquery(self):
        """Some beacons are split into position and status beacon. With this query we merge them into one beacon."""

        return """
        SELECT
            ST_AsEWKT(MAX(location)) AS location,
            MAX(altitude)  AS altitude,
            name,
            MAX(dstcall) AS dstcall,
            MAX(relay) AS relay,
            receiver_name,
            timestamp,
            MAX(track) AS track,
            MAX(ground_speed) AS ground_speed,

            MAX(address_type) AS address_type,
            MAX(aircraft_type) AS aircraft_type,
            CAST(MAX(CAST(stealth AS int)) AS boolean) AS stealth,
            MAX(address) AS address,
            MAX(climb_rate) AS climb_rate,
            MAX(turn_rate) AS turn_rate,
            MAX(signal_quality) AS signal_quality,
            MAX(error_count) AS error_count,
            MAX(frequency_offset) AS frequency_offset,
            MAX(gps_quality_horizontal) AS gps_quality_horizontal,
            MAX(gps_quality_vertical) AS gps_quality_vertical,
            MAX(software_version) AS software_version,
            MAX(hardware_version) AS hardware_version,
            MAX(real_address) AS real_address,
            MAX(signal_power) AS signal_power,

            CAST(MAX(distance) AS REAL) AS distance,
            CAST(MAX(radial) AS REAL) AS radial,
            CAST(MAX(quality) AS REAL) AS quality,
            CAST(MAX(agl) AS REAL) AS agl,
            MAX(location_mgrs) AS location_mgrs,
            MAX(location_mgrs_short) AS location_mgrs_short,

            MAX(receiver_id) AS receiver_id,
            MAX(device_id) AS device_id
        FROM "{0}" AS ab
        GROUP BY timestamp, name, receiver_name
        ORDER BY timestamp, name, receiver_name
        """.format(self.aircraft_table)

    def get_merged_receiver_beacons_subquery(self):
        """Some beacons are split into position and status beacon. With this query we merge them into one beacon."""

        return """
        SELECT
            ST_AsEWKT(MAX(location)) AS location,
            MAX(altitude) AS altitude,
            name,
            receiver_name,
            MAX(dstcall) AS dstcall,
            timestamp,

            MAX(version) AS version,
            MAX(platform) AS platform,
            MAX(cpu_load) AS cpu_load,
            MAX(free_ram) AS free_ram,
            MAX(total_ram) AS total_ram,
            MAX(ntp_error) AS ntp_error,
            MAX(rt_crystal_correction) AS rt_crystal_correction,
            MAX(voltage) AS voltage,
            MAX(amperage) AS amperage,
            MAX(cpu_temp) AS cpu_temp,
            MAX(senders_visible) AS senders_visible,
            MAX(senders_total) AS senders_total,
            MAX(rec_input_noise) AS rec_input_noise,
            MAX(senders_signal) AS senders_signal,
            MAX(senders_messages) AS senders_messages,
            MAX(good_senders_signal) AS good_senders_signal,
            MAX(good_senders) AS good_senders,
            MAX(good_and_bad_senders) AS good_and_bad_senders,

            MAX(receiver_id) AS receiver_id
        FROM "{0}" AS rb
        GROUP BY timestamp, name, receiver_name
        ORDER BY timestamp, name, receiver_name
        """.format(self.receiver_table)

    def is_transfered(self):
        query = """
        SELECT
            1
        FROM ({} LIMIT 1) AS sq, aircraft_beacons AS ab
        WHERE ab.timestamp = sq.timestamp AND ab.name = sq.name AND ab.receiver_name = sq.receiver_name;
        """.format(self.get_merged_aircraft_beacons_subquery())

        self.cur.execute(query)
        return len(self.cur.fetchall()) == 1

    def transfer_aircraft_beacons(self):
        query = """
        INSERT INTO aircraft_beacons(location, altitude, name, dstcall, relay, receiver_name, timestamp, track, ground_speed,
            address_type, aircraft_type, stealth, address, climb_rate, turn_rate, signal_quality, error_count, frequency_offset, gps_quality_horizontal, gps_quality_vertical, software_version, hardware_version, real_address, signal_power,
            distance, radial, quality, agl, location_mgrs, location_mgrs_short,
            receiver_id, device_id)
        {}
        ON CONFLICT DO NOTHING;
        """.format(self.get_merged_aircraft_beacons_subquery())

        self.cur.execute(query)
        self.conn.commit()

    def transfer_receiver_beacons(self):
        query = """
        INSERT INTO receiver_beacons(location, altitude, name, receiver_name, dstcall, timestamp,

            version, platform, cpu_load, free_ram, total_ram, ntp_error, rt_crystal_correction, voltage,
            amperage, cpu_temp, senders_visible, senders_total, rec_input_noise, senders_signal,
            senders_messages, good_senders_signal, good_senders, good_and_bad_senders,

            receiver_id)
        {}
        ON CONFLICT DO NOTHING;
        """.format(self.get_merged_receiver_beacons_subquery())

        self.cur.execute(query)
        self.conn.commit()

    def create_flights2d(self):
        query = """
        INSERT INTO flights2d
            (
                date,
                device_id,
                path
            )
        SELECT   sq5.date,
                 sq5.device_id,
                 st_collect(sq5.linestring order BY sq5.part) multilinestring
        FROM     (
            SELECT   sq4.timestamp::date AS date,
                     sq4.device_id,
                     sq4.part,
                     st_makeline(sq4.location ORDER BY sq4.timestamp) linestring
            FROM     (
                  SELECT   sq3.timestamp,
                           sq3.location,
                           sq3.device_id,
                           sum(sq3.ping) OVER (partition BY sq3.timestamp::date, sq3.device_id ORDER BY sq3.timestamp) part
                  FROM     (
                      SELECT sq2.t1 AS timestamp,
                             sq2.l1 AS location,
                             sq2.d1    device_id,
                             CASE
                                    WHEN sq2.t1 - sq2.t2 < interval'100s'
                                    AND    st_distancesphere(sq2.l1, sq2.l2) < 1000 THEN 0
                                    ELSE 1
                             END AS ping
                      FROM   (
                          SELECT   sq.timestamp                                                             t1,
                                   lag(sq.timestamp) OVER (partition BY sq.device_id ORDER BY sq.timestamp) t2,
                                   sq.location                                                              l1,
                                   lag(sq.location) OVER (partition BY sq.device_id ORDER BY sq.timestamp)  l2,
                                   sq.device_id                                                             d1,
                                   lag(sq.device_id) OVER (partition BY sq.device_id ORDER BY sq.timestamp) d2
                          FROM     (
                                SELECT   DISTINCT ON (device_id, timestamp) timestamp, device_id, location
                                FROM     {}
                                WHERE    device_id IS NOT NULL AND ground_speed > 250 AND agl < 100
                                ORDER BY device_id, timestamp, error_count) sq) sq2 ) sq3 ) sq4
                          GROUP BY sq4.timestamp::date,
                                   sq4.device_id,
                                   sq4.part ) sq5
        GROUP BY sq5.date,
                 sq5.device_id
        ON CONFLICT DO NOTHING;
        """.format(self.aircraft_table)

        self.cur.execute(query)
        self.conn.commit()

    def create_gaps2d(self):
        query = """
        INSERT INTO gaps2d(date, device_id, path)
        SELECT sq3.date,
            sq3.device_id,
            ST_Collect(sq3.path)
        FROM (
        SELECT
           sq2.t1::DATE AS date,
           sq2.d1 device_id,
           ST_MakeLine(sq2.l1, sq2.l2) path
        FROM
           (
              SELECT sq.timestamp t1,
                 LAG(sq.timestamp) OVER ( PARTITION BY sq.timestamp::DATE, sq.device_id ORDER BY sq.timestamp) t2,
                 sq.location l1,
                 LAG(sq.location) OVER ( PARTITION BY sq.timestamp::DATE, sq.device_id ORDER BY sq.timestamp) l2,
                 sq.device_id d1,
                 LAG(sq.device_id) OVER ( PARTITION BY sq.timestamp::DATE, sq.device_id ORDER BY sq.timestamp) d2,
                 sq.agl a1,
                 LAG(sq.agl) over ( PARTITION BY sq.timestamp::DATE, sq.device_id ORDER BY sq.timestamp) a2
              FROM
                 (
                    SELECT DISTINCT ON (device_id, timestamp) timestamp, device_id, location, agl
                    FROM {}
                    ORDER BY device_id, timestamp, error_count
                 ) sq
           ) sq2
        WHERE EXTRACT(epoch FROM sq2.t1 - sq2.t2) > 300
            AND ST_DistanceSphere(sq2.l1, sq2.l2) / EXTRACT(epoch FROM sq2.t1 - sq2.t2) BETWEEN 15 AND 50
            AND sq2.a1 > 300 AND sq2.a2 > 300
        ) sq3
        GROUP BY sq3.date, sq3.device_id
        ON CONFLICT DO NOTHING;
        """.format(self.aircraft_table)

        self.cur.execute(query)
        self.conn.commit()


def convert(sourcefile, datestr, saver):
    from ogn_python.gateway.process import string_to_message
    from ogn_python.gateway.process_tools import AIRCRAFT_BEACON_TYPES, RECEIVER_BEACON_TYPES
    from datetime import datetime

    fin = open_file(sourcefile)

    # get total lines of the input file
    total_lines = 0
    for line in fin:
        total_lines += 1
    fin.seek(0)

    current_line = 0
    steps = 100000
    reference_date = datetime.strptime(datestr + ' 12:00:00', '%Y-%m-%d %H:%M:%S')

    pbar = tqdm(fin, total=total_lines)
    for line in pbar:
        pbar.set_description('Importing {}'.format(sourcefile))

        current_line += 1
        if current_line % steps == 0:
            saver.flush()

        message = string_to_message(line.strip(), reference_date=reference_date)
        if message is None:
            continue

        dictfilt = lambda x, y: dict([(i, x[i]) for i in x if i in set(y)])

        try:
            if message['beacon_type'] in AIRCRAFT_BEACON_TYPES:
                message = dictfilt(message, ('beacon_type', 'aprs_type', 'location_wkt', 'altitude', 'name', 'dstcall', 'relay', 'receiver_name', 'timestamp', 'track', 'ground_speed',
                    'address_type', 'aircraft_type', 'stealth', 'address', 'climb_rate', 'turn_rate', 'signal_quality', 'error_count', 'frequency_offset', 'gps_quality_horizontal', 'gps_quality_vertical', 'software_version', 'hardware_version', 'real_address', 'signal_power',
                    'distance', 'radial', 'quality', 'agl', 'location_mgrs', 'location_mgrs_short',
                    'receiver_id', 'device_id'))

                beacon = AircraftBeacon(**message)
            elif message['beacon_type'] in RECEIVER_BEACON_TYPES:
                if 'rec_crystal_correction' in message:
                    del message['rec_crystal_correction']
                    del message['rec_crystal_correction_fine']
                beacon = ReceiverBeacon(**message)
            saver.add(beacon)
        except Exception as e:
            print(e)

    saver.flush()
    fin.close()


@user_cli.command('file_import')
@click.argument('path')
def file_import(path):
    """Import APRS logfiles into separate logfile tables."""

    import os
    import re

    # Get Filepaths and dates to import
    results = list()
    for (root, dirs, files) in os.walk(path):
        for file in sorted(files):
            match = re.match('OGN_log\.txt_([0-9]{4}\-[0-9]{2}\-[0-9]{2})\.gz$', file)
            if match:
                results.append({'filepath': os.path.join(root, file),
                                'datestr': match.group(1)})

    with LogfileDbSaver() as saver:
        already_imported = saver.get_datestrs()

        results = list(filter(lambda x: x['datestr'] not in already_imported, results))

        pbar = tqdm(results)
        for result in pbar:
            filepath = result['filepath']
            datestr = result['datestr']
            pbar.set_description("Importing data for {}".format(datestr))

            saver.set_datestr(datestr)
            saver.create_tables()
            convert(filepath, datestr, saver)
            saver.add_missing_devices()
            saver.add_missing_receivers()


@user_cli.command('update')
def update():
    """Update beacons (add foreign keys, compute distance, bearing, ags, etc.) in separate logfile tables."""

    with LogfileDbSaver() as saver:
        datestrs = saver.get_datestrs(no_index_only=True)
        pbar = tqdm(datestrs)
        for datestr in pbar:
            pbar.set_description("Updating relations for {}".format(datestr))
            saver.set_datestr(datestr)
            saver.update_receiver_location()
            saver.update_aircraft_beacons()
            saver.update_receiver_location()
            saver.create_indices()


@user_cli.command('transfer')
@click.argument('start')
@click.argument('end')
def transfer(start, end):
    """Transfer beacons from separate logfile tables to beacon table."""

    with LogfileDbSaver() as saver:
        if start is not None and end is not None:
            dates = get_database_days(start, end)
            datestrs = [date.strftime('%Y_%m_%d') for date in dates]
        else:
            datestrs = saver.get_datestrs()
        pbar = tqdm(datestrs)
        for datestr in pbar:
            pbar.set_description("Transfer beacons for {}".format(datestr))
            saver.set_datestr(datestr)
            if not saver.is_transfered():
                saver.transfer_aircraft_beacons()
                saver.transfer_receiver_beacons()


@user_cli.command('create_flights2d')
def create_flights2d():
    """Create complete flight traces from logfile tables."""

    with LogfileDbSaver() as saver:
        datestrs = saver.get_datestrs()
        pbar = tqdm(datestrs)
        for datestr in pbar:
            pbar.set_description("Create Flights2D for {}".format(datestr))
            saver.set_datestr(datestr)
            saver.create_flights2d()


@user_cli.command('create_gaps2d')
def create_gaps2d():
    """Create 'gaps' from logfile tables."""

    with LogfileDbSaver() as saver:
        datestrs = saver.get_datestrs()
        pbar = tqdm(datestrs)
        for datestr in pbar:
            pbar.set_description("Create Gaps2D for {}".format(datestr))
            saver.set_datestr(datestr)
            saver.create_gaps2d()


@user_cli.command('file_export')
@click.argument('path')
def file_export(path):
    """Export separate logfile tables to csv files. They can be used for fast bulk import with sql COPY command."""

    import os
    if not os.path.isdir(path):
        print("'{}' is not a path. Exiting")
        return

    with LogfileDbSaver() as saver:
        datestrs = saver.get_datestrs()
        datestrs = filter(lambda x: x.startswith('2018-12'), datestrs)
        pbar = tqdm(datestrs)
        for datestr in pbar:
            pbar.set_description("Exporting data for {}".format(datestr))
            saver.set_datestr(datestr)
            saver.export_to_path(path)

