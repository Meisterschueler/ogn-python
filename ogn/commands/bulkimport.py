import os
import re
import logging

from manager import Manager
from ogn.commands.dbutils import session
from ogn.model import AircraftBeacon, ReceiverBeacon
from ogn.utils import open_file
from ogn.gateway.process_tools import FileSaver, Converter, Merger


manager = Manager()

PATTERN = '^.+\.txt\_(\d{4}\-\d{2}\-\d{2})(\.gz)?$'


@manager.command
def convert_logfile(path):
    """Convert ogn logfiles to csv logfiles (one for aircraft beacons and one for receiver beacons) <arg: path>. Logfile name: blablabla.txt_YYYY-MM-DD."""

    logging.basicConfig(filename='convert.log', level=logging.DEBUG)

    if os.path.isfile(path):
        head, tail = os.path.split(path)
        convert(tail, path=head)
        logging.info("Finished converting single file {}".format(head))
    elif os.path.isdir(path):
        for filename in os.listdir(path):
            convert(filename, path=path)
        logging.info("Finished converting file path {}".format(path))
    else:
        logging.warning("Not a file nor a path: {}".format(path))


def convert(sourcefile, path=''):
    logging.info("convert: {} {}".format(sourcefile, path))
    import datetime

    from ogn.gateway.process import string_to_message

    match = re.search(PATTERN, sourcefile)
    if match:
        reference_date_string = match.group(1)
        reference_date = datetime.datetime.strptime(reference_date_string, "%Y-%m-%d")

        # Build the processing pipeline
        saver = FileSaver()
        converter = Converter(callback=saver)
        merger = Merger(callback=converter)

        try:
            saver.open(path, reference_date_string)
        except FileExistsError:
            logging.warning("Output files already exists. Skipping")
            return
    else:
        logging.warning("filename '{}' does not match pattern. Skipping".format(sourcefile))
        return

    fin = open_file(os.path.join(path, sourcefile))

    # get total lines of the input file
    total_lines = 0
    for line in fin:
        total_lines += 1
    fin.seek(0)

    progress = -1
    current_line = 0

    print('Start importing ogn-logfile')
    for line in fin:
        current_line += 1
        if int(1000 * current_line / total_lines) != progress:
            progress = round(1000 * current_line / total_lines)
            print("\rReading line {} ({}%)".format(current_line, progress / 10), end='')

        message = string_to_message(line.strip(), reference_date=reference_date)
        if message is None:
            print("=====")
            print(line.strip())
            continue
        
        merger.add_message(message)

    merger.flush()
    saver.close()

    fin.close()


@manager.command
def drop_indices():
    """Drop indices of AircraftBeacon."""
    session.execute("""
        DROP INDEX IF EXISTS idx_aircraft_beacons_location;
        DROP INDEX IF EXISTS ix_aircraft_beacons_date_device_id_address;
        DROP INDEX IF EXISTS ix_aircraft_beacons_date_receiver_id_distance;
        DROP INDEX IF EXISTS ix_aircraft_beacons_timestamp;
        
        DROP INDEX IF EXISTS idx_receiver_beacons_location;
        DROP INDEX IF EXISTS ix_receiver_beacons_date_receiver_id;
        DROP INDEX IF EXISTS ix_receiver_beacons_timestamp;
    """)
    print("Dropped indices of AircraftBeacon and ReceiverBeacon")

    # disable constraint trigger
    session.execute("""
        ALTER TABLE aircraft_beacons DISABLE TRIGGER ALL;
        ALTER TABLE receiver_beacons DISABLE TRIGGER ALL;
    """)
    session.commit()
    print("Disabled constraint triggers")


@manager.command
def create_indices():
    """Create indices for AircraftBeacon."""
    session.execute("""
        CREATE INDEX idx_aircraft_beacons_location ON aircraft_beacons USING GIST(location);
        CREATE INDEX ix_aircraft_beacons_date_device_id_address ON aircraft_beacons USING BTREE((timestamp::date), device_id, address);
        CREATE INDEX ix_aircraft_beacons_date_receiver_id_distance ON aircraft_beacons USING BTREE((timestamp::date), receiver_id, distance);
        CREATE INDEX ix_aircraft_beacons_timestamp ON aircraft_beacons USING BTREE(timestamp);
        
        CREATE INDEX idx_receiver_beacons_location ON receiver_beacons USING GIST(location);
        CREATE INDEX ix_receiver_beacons_date_receiver_id ON receiver_beacons USING BTREE((timestamp::date), receiver_id);
        CREATE INDEX ix_receiver_beacons_timestamp ON receiver_beacons USING BTREE(timestamp);
    """)
    print("Created indices for AircraftBeacon and ReceiverBeacon")

    session.execute("""
        ALTER TABLE aircraft_beacons ENABLE TRIGGER ALL;
        ALTER TABLE receiver_beacons ENABLE TRIGGER ALL;
    """)
    session.commit()
    print("Enabled constraint triggers")


@manager.command
def import_csv_logfile(path, logfile='main.log', loglevel='INFO'):
    """Import csv logfile <arg: csv logfile>."""

    import datetime

    import os
    if os.path.isfile(path):
        print("{}: Importing file: {}".format(datetime.datetime.now(), path))
        import_logfile(path)
    elif os.path.isdir(path):
        print("{}: Scanning path: {}".format(datetime.datetime.now(), path))
        for filename in os.listdir(path):
            print("{}: Importing file: {}".format(datetime.datetime.now(), filename))
            import_logfile(os.path.join(path, filename))
    else:
        print("{}: Path {} not found.".format(datetime.datetime.now(), path))

    print("{}: Finished.".format(datetime.datetime.now()))


def import_logfile(path):
    import os
    import re

    head, tail = os.path.split(path)
    match = re.search('^.+\.csv\_(\d{4}\-\d{2}\-\d{2}).+?$', tail)
    if match:
        reference_date_string = match.group(1)
    else:
        print("filename '{}' does not match pattern. Skipping".format(path))
        return

    f = open_file(path)
    header = f.readline().strip()
    f.close()

    aircraft_beacon_header = ','.join(AircraftBeacon.get_csv_columns())
    receiver_beacon_header = ','.join(ReceiverBeacon.get_csv_columns())

    if header == aircraft_beacon_header:
        if check_no_beacons('aircraft_beacons', reference_date_string):
            import_aircraft_beacon_logfile(path)
        else:
            print("For {} beacons already exist. Skipping".format(reference_date_string))
    elif header == receiver_beacon_header:
        if check_no_beacons('receiver_beacons', reference_date_string):
            import_receiver_beacon_logfile(path)
        else:
            print("For {} beacons already exist. Skipping".format(reference_date_string))
    else:
        s1 = header
        s2 = ','.join(AircraftBeacon.get_csv_columns())
        print(s1)
        print(s2)
        print([i for i in range(len(s1)) if s1[i] != s2[i]])
        print("Unknown file type: {}".format(tail))


def check_no_beacons(tablename, reference_date_string):
    result = session.execute("""SELECT * FROM {0} WHERE timestamp BETWEEN '{1} 00:00:00' AND '{1} 23:59:59' LIMIT 1""".format(tablename, reference_date_string))
    if result.fetchall():
        return False
    else:
        return True


def import_aircraft_beacon_logfile(csv_logfile):
    SQL_TEMPTABLE_STATEMENT = """
    DROP TABLE IF EXISTS aircraft_beacons_temp;
    CREATE TABLE aircraft_beacons_temp(
        location geometry,
        altitude real,
        name character varying,
        dstcall character varying,
        relay character varying,
        receiver_name character varying(9),
        "timestamp" timestamp without time zone,
        track smallint,
        ground_speed real,

        address_type smallint,
        aircraft_type smallint,
        stealth boolean,
        address character varying,
        climb_rate real,
        turn_rate real,
        signal_quality real,
        error_count smallint,
        frequency_offset real,
        gps_quality_horizontal smallint,
        gps_quality_vertical smallint,
        software_version real,
        hardware_version smallint,
        real_address character varying(6),
        signal_power real,

        distance real,
        radial smallint,
        normalized_signal_quality real,
        location_mgrs character varying(15)
        );
    """

    session.execute(SQL_TEMPTABLE_STATEMENT)

    SQL_COPY_STATEMENT = """
    COPY aircraft_beacons_temp(%s) FROM STDIN WITH
        CSV
        HEADER
        DELIMITER AS ','
    """

    file = open_file(csv_logfile)
    column_names = ','.join(AircraftBeacon.get_csv_columns())
    sql = SQL_COPY_STATEMENT % column_names

    print("Start importing logfile: {}".format(csv_logfile))

    conn = session.connection().connection
    cursor = conn.cursor()
    cursor.copy_expert(sql=sql, file=file)
    conn.commit()
    cursor.close()
    file.close()
    print("Read logfile into temporary table")

    # create device if not exist
    session.execute("""
        INSERT INTO devices(address)
        SELECT DISTINCT(t.address)
        FROM aircraft_beacons_temp t
        WHERE NOT EXISTS (SELECT 1 FROM devices d WHERE d.address = t.address)
    """)
    print("Inserted missing Devices")

    # create receiver if not exist
    session.execute("""
        INSERT INTO receivers(name)
        SELECT DISTINCT(t.receiver_name)
        FROM aircraft_beacons_temp t
        WHERE NOT EXISTS (SELECT 1 FROM receivers r WHERE r.name = t.receiver_name)
    """)
    print("Inserted missing Receivers")

    session.execute("""
        INSERT INTO aircraft_beacons(location, altitude, name, dstcall, relay, receiver_name, timestamp, track, ground_speed,
                                    address_type, aircraft_type, stealth, address, climb_rate, turn_rate, signal_quality, error_count, frequency_offset, gps_quality_horizontal, gps_quality_vertical, software_version, hardware_version, real_address, signal_power,
                                    distance, radial, normalized_signal_quality, location_mgrs,
                                    receiver_id, device_id)
        SELECT t.location, t.altitude, t.name, t.dstcall, t.relay, t.receiver_name, t.timestamp, t.track, t.ground_speed,
               t.address_type, t.aircraft_type, t.stealth, t.address, t.climb_rate, t.turn_rate, t.signal_quality, t.error_count, t.frequency_offset, t.gps_quality_horizontal, t.gps_quality_vertical, t.software_version, t.hardware_version, t.real_address, t.signal_power,
               t.distance, t.radial, t.normalized_signal_quality, t.location_mgrs,
               r.id, d.id
        FROM aircraft_beacons_temp t, receivers r, devices d
        WHERE t.receiver_name = r.name AND t.address = d.address
    """)
    print("Wrote AircraftBeacons from temporary table into final table")

    session.execute("""DROP TABLE aircraft_beacons_temp""")
    print("Dropped temporary table")

    session.commit()
    print("Finished")


def import_receiver_beacon_logfile(csv_logfile):
    """Import csv logfile <arg: csv logfile>."""

    SQL_TEMPTABLE_STATEMENT = """
    DROP TABLE IF EXISTS receiver_beacons_temp;
    CREATE TABLE receiver_beacons_temp(
        location geometry,
        altitude real,
        name character varying,
        receiver_name character varying(9),
        dstcall character varying,
        "timestamp" timestamp without time zone,

        version character varying,
        platform character varying,
        cpu_load real,
        free_ram real,
        total_ram real,
        ntp_error real,
        rt_crystal_correction real,
        voltage real,
        amperage real,
        cpu_temp real,
        senders_visible integer,
        senders_total integer,
        rec_input_noise real,
        senders_signal real,
        senders_messages integer,
        good_senders_signal real,
        good_senders integer,
        good_and_bad_senders integer
        );
    """

    session.execute(SQL_TEMPTABLE_STATEMENT)

    SQL_COPY_STATEMENT = """
    COPY receiver_beacons_temp(%s) FROM STDIN WITH
        CSV
        HEADER
        DELIMITER AS ','
    """

    file = open_file(csv_logfile)
    column_names = ','.join(ReceiverBeacon.get_csv_columns())
    sql = SQL_COPY_STATEMENT % column_names

    print("Start importing logfile: {}".format(csv_logfile))

    conn = session.connection().connection
    cursor = conn.cursor()
    cursor.copy_expert(sql=sql, file=file)
    conn.commit()
    cursor.close()
    file.close()
    print("Read logfile into temporary table")

    # create receiver if not exist
    session.execute("""
        INSERT INTO receivers(name)
        SELECT DISTINCT(t.name)
        FROM receiver_beacons_temp t
        WHERE NOT EXISTS (SELECT 1 FROM receivers r WHERE r.name = t.name)
    """)
    print("Inserted missing Receivers")

    session.execute("""
        INSERT INTO receiver_beacons(location, altitude, name, dstcall, receiver_name, timestamp,
                                    version, platform, cpu_load, free_ram, total_ram, ntp_error, rt_crystal_correction, voltage,amperage, cpu_temp, senders_visible, senders_total, rec_input_noise, senders_signal, senders_messages, good_senders_signal, good_senders, good_and_bad_senders,
                                    receiver_id)
        SELECT t.location, t.altitude, t.name, t.dstcall, t.receiver_name, t.timestamp,
               t.version, t.platform, t.cpu_load, t.free_ram, t.total_ram, t.ntp_error, t.rt_crystal_correction, t.voltage,amperage, t.cpu_temp, t.senders_visible, t.senders_total, t.rec_input_noise, t.senders_signal, t.senders_messages, t.good_senders_signal, t.good_senders, t.good_and_bad_senders,
               r.id
        FROM receiver_beacons_temp t, receivers r
        WHERE t.name = r.name
    """)
    print("Wrote ReceiverBeacons from temporary table into final table")

    session.execute("""DROP TABLE receiver_beacons_temp""")
    print("Dropped temporary table")

    session.commit()
    print("Finished")
