from manager import Manager
from ogn.collect.database import update_device_infos, update_country_code
from ogn.commands.dbutils import engine, session
from ogn.model import Base, DeviceInfoOrigin
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
    session.execute('CREATE EXTENSION IF NOT EXISTS btree_gist;')
    session.execute('CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;')
    session.commit()
    Base.metadata.create_all(engine)
    session.execute("SELECT create_hypertable('aircraft_beacons', 'timestamp', chunk_target_size => '2GB');")
    session.execute("SELECT create_hypertable('receiver_beacons', 'timestamp', chunk_target_size => '2GB');")
    session.commit()
    #alembic_cfg = Config(ALEMBIC_CONFIG_FILE)
    #command.stamp(alembic_cfg, "head")
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
    counter = update_device_infos(session, DeviceInfoOrigin.ogn_ddb)
    print("Imported %i devices." % counter)


@manager.command
def import_file(path='tests/custom_ddb.txt'):
    """Import registered devices from a local file."""

    print("Import registered devices from '{}'...".format(path))
    counter = update_device_infos(session,
                                  DeviceInfoOrigin.user_defined,
                                  path=path)
    print("Imported %i devices." % counter)

@manager.command
def import_flarmnet(path='tests/data.fln'):
    """Import registered devices from a local file."""

    print("Import registered devices from '{}'...".format("internet" if path is None else path))
    counter = update_device_infos(session,
                                  DeviceInfoOrigin.flarmnet,
                                  path=path)
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
def update_country_codes():
    """Update country codes of all receivers."""
    
    update_country_code(session=session)