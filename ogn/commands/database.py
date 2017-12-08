from manager import Manager
from ogn.collect.database import update_device_infos
from ogn.commands.dbutils import engine, session
from ogn.model import Base, DeviceInfoOrigin, AircraftBeacon, ReceiverBeacon
from ogn.utils import get_airports
from sqlalchemy import distinct
from sqlalchemy.sql import null, func


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
def update_receivers():
    from ogn.collect.database import update_receivers as ur
    ur()


@manager.command
def update_receiver_stats():
    """Add/update entries in receiver stats table."""

    asdf = session.query(
        ReceiverBeacon.receiver_id,
        func.count(distinct(AircraftBeacon.device_id)).label('device_count'),
        func.max(AircraftBeacon.altitude).label('max_altitude'),
        func.max(func.ST_Distance(AircraftBeacon.location_wkt, AircraftBeacon.location_wkt)).label('max_distance')) \
        .filter(ReceiverBeacon.receiver_id == AircraftBeacon.receiver_id) \
        .group_by(ReceiverBeacon.id)

    print(asdf)
    for a in asdf.all():
        print(a)

    return

    asdf = session.query(distinct(ReceiverBeacon.receiver_id), func.DATE(ReceiverBeacon.timestamp).label('date')) \
        .filter(ReceiverBeacon.receiver_id != null())
