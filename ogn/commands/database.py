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
