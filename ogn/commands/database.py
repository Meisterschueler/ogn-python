from manager import Manager
from ogn.collect.database import update_device_infos
from ogn.commands.dbutils import engine, session
from ogn.model import Base, DeviceInfoOrigin, AircraftBeacon, ReceiverBeacon, Device, Receiver
from ogn.utils import get_airports
from sqlalchemy import insert, distinct
from sqlalchemy.sql import null, and_, or_, func, not_
from sqlalchemy.sql.expression import case

from ogn.utils import get_country_code


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
    address_origin = DeviceInfoOrigin.ogn_ddb
    counter = update_device_infos(session,
                                  address_origin)
    print("Imported %i devices." % counter)


@manager.command
def import_file(path='tests/custom_ddb.txt'):
    """Import registered devices from a local file."""
    # (flushes previously manually imported entries)

    print("Import registered devices from '{}'...".format(path))
    address_origin = DeviceInfoOrigin.user_defined
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
def update_devices():
    """Add/update entries in devices table and update foreign keys in aircraft beacons."""

    # Create missing Device from AircraftBeacon
    available_devices = session.query(Device.address) \
        .subquery()

    missing_devices_query = session.query(distinct(AircraftBeacon.address)) \
        .filter(AircraftBeacon.device_id == null()) \
        .filter(~AircraftBeacon.address.in_(available_devices))

    ins = insert(Device).from_select([Device.address], missing_devices_query)
    res = session.execute(ins)
    insert_count = res.rowcount

    # Update relations to aircraft beacons
    upd = session.query(AircraftBeacon) \
        .filter(AircraftBeacon.device_id == null()) \
        .filter(AircraftBeacon.address == Device.address) \
        .update({AircraftBeacon.device_id: Device.id},
                synchronize_session='fetch')

    session.commit()
    print("Inserted {} Devices".format(insert_count))
    print("Updated {} AircraftBeacons".format(upd))


@manager.command
def update_receivers():
    """Add/update_receivers entries in receiver table and update_receivers foreign keys in aircraft beacons and receiver beacons."""
    # Create missing Receiver from ReceiverBeacon
    available_receivers = session.query(Receiver.name) \
        .subquery()

    missing_receiver_query = session.query(distinct(ReceiverBeacon.name)) \
        .filter(ReceiverBeacon.receiver_id == null()) \
        .filter(~ReceiverBeacon.name.in_(available_receivers))

    ins = insert(Receiver).from_select([Receiver.name], missing_receiver_query)
    res = session.execute(ins)
    insert_count = res.rowcount

    # Update missing or changed values, update_receivers them and set country code to None if location changed
    new_values_range = session.query(ReceiverBeacon.name,
                                     func.min(ReceiverBeacon.timestamp).label('firstseen'),
                                     func.max(ReceiverBeacon.timestamp).label('lastseen')) \
                              .filter(ReceiverBeacon.receiver_id == null()) \
                              .group_by(ReceiverBeacon.name) \
                              .subquery()

    last_values = session.query(ReceiverBeacon.name,
                                func.max(new_values_range.c.firstseen).label('firstseen'),
                                func.max(new_values_range.c.lastseen).label('lastseen'),
                                func.max(ReceiverBeacon.location_wkt).label('location_wkt'),
                                func.max(ReceiverBeacon.altitude).label('altitude'),
                                func.max(ReceiverBeacon.version).label('version'),
                                func.max(ReceiverBeacon.platform).label('platform')) \
                         .filter(and_(ReceiverBeacon.name == new_values_range.c.name,
                                      ReceiverBeacon.timestamp == new_values_range.c.lastseen)) \
                         .group_by(ReceiverBeacon.name) \
                         .subquery()

    last_valid_values = session.query(last_values) \
                               .filter(and_(last_values.c.firstseen != null(),
                                            last_values.c.lastseen != null(),
                                            last_values.c.location_wkt != null(),
                                            last_values.c.altitude != null(),
                                            last_values.c.version != null(),
                                            last_values.c.platform != null())) \
                               .subquery()

    update_values = session.query(Receiver.name,
                                  case([(or_(Receiver.firstseen == null(), Receiver.firstseen > last_valid_values.c.firstseen), last_valid_values.c.firstseen),
                                        (Receiver.firstseen <= last_valid_values.c.firstseen, Receiver.firstseen)]).label('firstseen'),
                                  case([(or_(Receiver.lastseen == null(), Receiver.lastseen < last_valid_values.c.lastseen), last_valid_values.c.lastseen),
                                        (Receiver.firstseen >= last_valid_values.c.firstseen, Receiver.firstseen)]).label('lastseen'),
                                  case([(or_(Receiver.lastseen == null(), Receiver.lastseen < last_valid_values.c.lastseen), func.ST_Transform(last_valid_values.c.location_wkt, 4326)),
                                        (Receiver.lastseen >= last_valid_values.c.lastseen, func.ST_Transform(Receiver.location_wkt, 4326))]).label('location_wkt'),
                                  case([(or_(Receiver.lastseen == null(), Receiver.lastseen < last_valid_values.c.lastseen), last_valid_values.c.altitude),
                                        (Receiver.lastseen >= last_valid_values.c.lastseen, Receiver.altitude)]).label('altitude'),
                                  case([(or_(Receiver.lastseen == null(), Receiver.lastseen < last_valid_values.c.lastseen), last_valid_values.c.version),
                                        (Receiver.lastseen >= last_valid_values.c.lastseen, Receiver.version)]).label('version'),
                                  case([(or_(Receiver.lastseen == null(), Receiver.lastseen < last_valid_values.c.lastseen), last_valid_values.c.platform),
                                        (Receiver.lastseen >= last_valid_values.c.lastseen, Receiver.platform)]).label('platform'),
                                  case([(or_(Receiver.location_wkt == null(), not_(func.ST_Equals(Receiver.location_wkt, last_valid_values.c.location_wkt))), None),
                                        (func.ST_Equals(Receiver.location_wkt, last_valid_values.c.location_wkt), Receiver.country_code)]).label('country_code')) \
                           .filter(Receiver.name == last_valid_values.c.name) \
                           .subquery()

    update_receivers = session.query(Receiver) \
        .filter(Receiver.name == update_values.c.name) \
        .update({Receiver.firstseen: update_values.c.firstseen,
                 Receiver.lastseen: update_values.c.lastseen,
                 Receiver.location_wkt: update_values.c.location_wkt,
                 Receiver.altitude: update_values.c.altitude,
                 Receiver.version: update_values.c.version,
                 Receiver.platform: update_values.c.platform,
                 Receiver.country_code: update_values.c.country_code},
                synchronize_session='fetch')

    # Update relations to aircraft beacons
    update_aircraft_beacons = session.query(AircraftBeacon) \
        .filter(and_(AircraftBeacon.receiver_id == null(), AircraftBeacon.receiver_name == Receiver.name)) \
        .update({AircraftBeacon.receiver_id: Receiver.id},
                synchronize_session='fetch')

    # Update relations to receiver beacons
    update_receiver_beacons = session.query(ReceiverBeacon) \
        .filter(and_(ReceiverBeacon.receiver_id == null(), ReceiverBeacon.name == Receiver.name)) \
        .update({ReceiverBeacon.receiver_id: Receiver.id},
                synchronize_session='fetch')

    session.commit()

    print("Receivers: {} inserted, {} updated.".format(insert_count, update_receivers))
    print("Updated relations: {} aircraft beacons, {} receiver beacons".format(update_aircraft_beacons, update_receiver_beacons))


@manager.command
def update_country_code():
    # update country code if None
    unknown_country_query = session.query(Receiver) \
        .filter(Receiver.country_code == null()) \
        .filter(Receiver.location_wkt != null()) \
        .order_by(Receiver.name)

    for receiver in unknown_country_query.all():
        location = receiver.location
        country_code = get_country_code(location.latitude, location.longitude)
        if country_code is not None:
            receiver.country_code = country_code
            print("Updated country_code for {} to {}".format(receiver.name, receiver.country_code))

    session.commit()
