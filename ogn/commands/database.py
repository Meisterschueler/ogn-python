from ogn.commands.dbutils import engine, session
from ogn.model import Base, AddressOrigin, AircraftBeacon, ReceiverBeacon, Device, Receiver
from ogn.utils import get_airports
from ogn.collect.database import update_device_infos

from sqlalchemy import insert, distinct
from sqlalchemy.sql import null

from manager import Manager
manager = Manager()

ALEMBIC_CONFIG_FILE = "alembic.ini"


@manager.command
def init():
    """Initialize the database."""

    from alembic.config import Config
    from alembic import command

    session.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
    session.commit()
    Base.metadata.create_all(engine)
    alembic_cfg = Config(ALEMBIC_CONFIG_FILE)
    command.stamp(alembic_cfg, "head")
    print("Done.")


@manager.command
def upgrade():
    """Upgrade database to the latest version."""

    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(ALEMBIC_CONFIG_FILE)
    command.upgrade(alembic_cfg, 'head')


@manager.command
def drop(sure='n'):
    """Drop all tables."""
    if sure == 'y':
        Base.metadata.drop_all(engine)
        print('Dropped all tables.')
    else:
        print("Add argument '--sure y' to drop all tables.")


@manager.command
def import_ddb():
    """Import registered devices from the DDB."""

    print("Import registered devices fom the DDB...")
    address_origin = AddressOrigin.ogn_ddb
    counter = update_device_infos(session,
                                  address_origin)
    print("Imported %i devices." % counter)


@manager.command
def import_file(path='tests/custom_ddb.txt'):
    """Import registered devices from a local file."""
    # (flushes previously manually imported entries)

    print("Import registered devices from '{}'...".format(path))
    address_origin = AddressOrigin.user_defined
    counter = update_device_infos(session,
                                  address_origin,
                                  csvfile=path)
    print("Imported %i devices." % counter)


@manager.command
def import_airports(path='tests/SeeYou.cup'):
    """Import airports from a ".cup" file"""

    print("Import airports from '{}'...".format(path))
    airports = get_airports(path)
    session.bulk_save_objects(airports)
    session.commit()
    print("Imported {} airports.".format(len(airports)))


@manager.command
def update_relations():
    """Update AircraftBeacon and ReceiverBeacon relations"""

    # Create missing Receiver from ReceiverBeacon
    available_receivers = session.query(Receiver.name) \
        .subquery()

    missing_receiver_query = session.query(distinct(ReceiverBeacon.name)) \
        .filter(ReceiverBeacon.receiver_id == null()) \
        .filter(~ReceiverBeacon.name.in_(available_receivers))

    ins = insert(Receiver).from_select([Receiver.name], missing_receiver_query)
    session.execute(ins)

    # Create missing Device from AircraftBeacon
    available_addresses = session.query(Device.address) \
        .subquery()

    missing_addresses_query = session.query(distinct(AircraftBeacon.address)) \
        .filter(AircraftBeacon.device_id == null()) \
        .filter(~AircraftBeacon.address.in_(available_addresses))

    ins2 = insert(Device).from_select([Device.address], missing_addresses_query)
    session.execute(ins2)
    session.commit()
    print("Inserted {} Receivers and {} Devices".format(ins, ins2))
    return

    # Update AircraftBeacons
    upd = session.query(AircraftBeacon) \
        .filter(AircraftBeacon.device_id == null()) \
        .filter(AircraftBeacon.receiver_id == null()) \
        .filter(AircraftBeacon.address == Device.address) \
        .filter(AircraftBeacon.receiver_name == Receiver.name) \
        .update({AircraftBeacon.device_id: Device.id,
                 AircraftBeacon.receiver_id: Receiver.id},
                synchronize_session='fetch')

    upd2 = session.query(ReceiverBeacon) \
        .filter(ReceiverBeacon.receiver_id == null()) \
        .filter(ReceiverBeacon.receiver_name == Receiver.name) \
        .update({Receiver.name: ReceiverBeacon.receiver_name},
                synchronize_session='fetch')

    session.commit()
    print("Updated {} AircraftBeacons and {} ReceiverBeacons".
          format(upd, upd2))


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
    f = open(path, 'r')
    try:
        header = f.readline().strip()
    except UnicodeDecodeError as e:
        print("Not a text file: {}".format(path))
        f.close()
        return
    f.close()

    aircraft_beacon_header = ','.join(AircraftBeacon.get_csv_columns())
    receiver_beacon_header = ','.join(ReceiverBeacon.get_csv_columns())

    if header == aircraft_beacon_header:
        import_aircraft_beacon_logfile(path)
    elif header == receiver_beacon_header:
        import_receiver_beacon_logfile(path)
    else:
        print("Unknown file type: {}".format())


def import_aircraft_beacon_logfile(csv_logfile):
    SQL_TEMPTABLE_STATEMENT = """
    CREATE TABLE aircraft_beacon_temp(
        location geometry,
        altitude integer,
        name character varying,
        receiver_name character varying(9),
        "timestamp" timestamp without time zone,
        track integer,
        ground_speed double precision,

        address_type smallint,
        aircraft_type smallint,
        stealth boolean,
        address character varying(6),
        climb_rate double precision,
        turn_rate double precision,
        flightlevel double precision,
        signal_quality double precision,
        error_count integer,
        frequency_offset double precision,
        gps_status character varying,
        software_version double precision,
        hardware_version smallint,
        real_address character varying(6),
        signal_power double precision
        )
    """

    session.execute(SQL_TEMPTABLE_STATEMENT)

    SQL_COPY_STATEMENT = """
    COPY aircraft_beacon_temp(%s) FROM STDIN WITH
        CSV
        HEADER
        DELIMITER AS ','
    """

    file = open(csv_logfile, 'r')
    column_names = ','.join(AircraftBeacon.get_csv_columns())
    sql = SQL_COPY_STATEMENT % column_names

    print("Start importing logfile: {}".format(csv_logfile))

    conn = session.connection().connection
    cursor = conn.cursor()
    cursor.copy_expert(sql=sql, file=file)
    conn.commit()
    cursor.close()
    print("Read logfile into temporary table")

    # create device if not exist
    session.execute("""
        INSERT INTO device(address)
        SELECT DISTINCT(t.address)
        FROM aircraft_beacon_temp t
        WHERE NOT EXISTS (SELECT 1 FROM device d WHERE d.address = t.address)
    """)
    print("Inserted missing Devices")

    # create receiver if not exist
    session.execute("""
        INSERT INTO receiver(name)
        SELECT DISTINCT(t.receiver_name)
        FROM aircraft_beacon_temp t
        WHERE NOT EXISTS (SELECT 1 FROM receiver r WHERE r.name = t.receiver_name)
    """)
    print("Inserted missing Receivers")

    session.execute("""
        INSERT INTO aircraft_beacon(location, altitude, name, receiver_name, timestamp, track, ground_speed,
                                    address_type, aircraft_type, stealth, address, climb_rate, turn_rate, flightlevel, signal_quality, error_count, frequency_offset, gps_status, software_version, hardware_version, real_address, signal_power,
                                   status, receiver_id, device_id)
        SELECT t.location, t.altitude, t.name, t.receiver_name, t.timestamp, t.track, t.ground_speed,
               t.address_type, t.aircraft_type, t.stealth, t.address, t.climb_rate, t.turn_rate, t.flightlevel, t.signal_quality, t.error_count, t.frequency_offset, t.gps_status, t.software_version, t.hardware_version, t.real_address, t.signal_power,
               0, r.id, d.id
        FROM aircraft_beacon_temp t, receiver r, device d
        WHERE t.receiver_name = r.name AND t.address = d.address
    """)
    print("Wrote AircraftBeacons from temporary table into final table")

    session.execute("""DROP TABLE aircraft_beacon_temp""")
    print("Dropped temporary table")

    session.commit()
    print("Finished")


def import_receiver_beacon_logfile(csv_logfile):
    """Import csv logfile <arg: csv logfile>."""

    SQL_TEMPTABLE_STATEMENT = """
    CREATE TABLE receiver_beacon_temp(
        location geometry,
        altitude integer,
        name character varying,
        receiver_name character varying(9),
        "timestamp" timestamp without time zone,
        track integer,
        ground_speed double precision,

        version character varying,
        platform character varying,
        cpu_load double precision,
        free_ram double precision,
        total_ram double precision,
        ntp_error double precision,
        rt_crystal_correction double precision,
        voltage double precision,
        amperage double precision,
        cpu_temp double precision,
        senders_visible integer,
        senders_total integer,
        rec_input_noise double precision,
        senders_signal double precision,
        senders_messages integer,
        good_senders_signal double precision,
        good_senders integer,
        good_and_bad_senders integer
        )
    """

    session.execute(SQL_TEMPTABLE_STATEMENT)

    SQL_COPY_STATEMENT = """
    COPY receiver_beacon_temp(%s) FROM STDIN WITH
        CSV
        HEADER
        DELIMITER AS ','
    """

    file = open(csv_logfile, 'r')
    column_names = ','.join(ReceiverBeacon.get_csv_columns())
    sql = SQL_COPY_STATEMENT % column_names

    print("Start importing logfile: {}".format(csv_logfile))

    conn = session.connection().connection
    cursor = conn.cursor()
    cursor.copy_expert(sql=sql, file=file)
    conn.commit()
    cursor.close()
    print("Read logfile into temporary table")

    # create receiver if not exist
    session.execute("""
        INSERT INTO receiver(name)
        SELECT DISTINCT(t.name)
        FROM receiver_beacon_temp t
        WHERE NOT EXISTS (SELECT 1 FROM receiver r WHERE r.name = t.name)
    """)
    print("Inserted missing Receivers")

    session.execute("""
        INSERT INTO receiver_beacon(location, altitude, name, receiver_name, timestamp, track, ground_speed,
                                    version, platform, cpu_load, free_ram, total_ram, ntp_error, rt_crystal_correction, voltage,amperage, cpu_temp, senders_visible, senders_total, rec_input_noise, senders_signal, senders_messages, good_senders_signal, good_senders, good_and_bad_senders,
                                    status, receiver_id)
        SELECT t.location, t.altitude, t.name, t.receiver_name, t.timestamp, t.track, t.ground_speed,
               t.version, t.platform, t.cpu_load, t.free_ram, t.total_ram, t.ntp_error, t.rt_crystal_correction, t.voltage,amperage, t.cpu_temp, t.senders_visible, t.senders_total, t.rec_input_noise, t.senders_signal, t.senders_messages, t.good_senders_signal, t.good_senders, t.good_and_bad_senders,
               0, r.id
        FROM receiver_beacon_temp t, receiver r
        WHERE t.name = r.name
    """)
    print("Wrote ReceiverBeacons from temporary table into final table")

    session.execute("""DROP TABLE receiver_beacon_temp""")
    print("Dropped temporary table")

    session.commit()
    print("Finished")
