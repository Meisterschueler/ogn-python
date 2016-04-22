from ogn.commands.dbutils import engine, session
from ogn.model import Base, AddressOrigin
from ogn.utils import get_ddb, get_airports
from ogn.collect.database import update_devices

from manager import Manager
manager = Manager()

ALEMBIC_CONFIG_FILE = "alembic.ini"


@manager.command
def init():
    """Initialize the database."""

    from alembic.config import Config
    from alembic import command

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
    counter = update_devices(session, AddressOrigin.ogn_ddb, get_ddb())
    print("Imported %i devices." % counter)


@manager.command
def import_file(path='tests/custom_ddb.txt'):
    """Import registered devices from a local file."""
    # (flushes previously manually imported entries)

    print("Import registered devices from '{}'...".format(path))
    counter = update_devices(session, AddressOrigin.user_defined,
                             get_ddb(path))
    print("Imported %i devices." % counter)


@manager.command
def import_airports(path='tests/Germany.cup'):
    """Import airports from a ".cup" file"""

    print("Import airports from '{}'...".format(path))
    airports = get_airports(path)
    session.bulk_save_objects(airports)
    session.commit()
    print("Imported {} airports.".format(len(airports)))
