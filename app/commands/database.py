from flask import current_app
from flask.cli import AppGroup
import click

from datetime import datetime, timedelta
from sqlalchemy.sql import func

from app.collect.database import update_device_infos, update_country_code
from app.model import *
from app.utils import get_airports, get_days

from app import db

user_cli = AppGroup("database")
user_cli.help = "Database creation and handling."


ALEMBIC_CONFIG_FILE = "alembic.ini"


def get_database_days(start, end):
    """Returns the first and the last day in aircraft_beacons table."""

    if start is None and end is None:
        days_from_db = db.session.query(func.min(AircraftBeacon.timestamp).label("first_day"), func.max(AircraftBeacon.timestamp).label("last_day")).one()
        start = days_from_db[0].date()
        end = days_from_db[1].date()
    else:
        start = datetime.strptime(start, "%Y-%m-%d").date()
        end = datetime.strptime(end, "%Y-%m-%d").date()

    days = get_days(start, end)

    return days


@user_cli.command("info")
def info():
    print(current_app.config)
    print(current_app.config["SQLALCHEMY_DATABASE_URI"])


@user_cli.command("init")
def init():
    """Initialize the database."""

    from alembic.config import Config
    from alembic import command

    db.session.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    db.session.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
    db.session.commit()
    db.create_all()

    # alembic_cfg = Config(ALEMBIC_CONFIG_FILE)
    # command.stamp(alembic_cfg, "head")
    print("Done.")


@user_cli.command("init_timescaledb")
def init_timescaledb():
    """Initialize TimescaleDB features."""

    db.session.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
    db.session.execute("SELECT create_hypertable('aircraft_beacons', 'timestamp', chunk_target_size => '2GB', if_not_exists => TRUE);")
    db.session.execute("SELECT create_hypertable('receiver_beacons', 'timestamp', chunk_target_size => '2GB', if_not_exists => TRUE);")
    db.session.commit()


@user_cli.command("upgrade")
def upgrade():
    """Upgrade database to the latest version."""

    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(ALEMBIC_CONFIG_FILE)
    command.upgrade(alembic_cfg, "head")


@user_cli.command("drop")
@click.option("--sure", default="n")
def drop(sure):
    """Drop all tables."""
    if sure == "y":
        db.drop_all()
        print("Dropped all tables.")
    else:
        print("Add argument '--sure y' to drop all tables.")


@user_cli.command("import_ddb")
def import_ddb():
    """Import registered devices from the DDB."""

    print("Import registered devices fom the DDB...")
    counter = update_device_infos(db.session, DeviceInfoOrigin.ogn_ddb)
    print("Imported %i devices." % counter)


@user_cli.command("import_file")
@click.argument("path")
def import_file(path="tests/custom_ddb.txt"):
    """Import registered devices from a local file."""

    print("Import registered devices from '{}'...".format(path))
    counter = update_device_infos(db.session, DeviceInfoOrigin.user_defined, path=path)
    print("Imported %i devices." % counter)


@user_cli.command("import_flarmnet")
@click.argument("path")
def import_flarmnet(path=None):
    """Import registered devices from a local file."""

    print("Import registered devices from '{}'...".format("internet" if path is None else path))
    counter = update_device_infos(db.session, DeviceInfoOrigin.flarmnet, path=path)
    print("Imported %i devices." % counter)


@user_cli.command("import_airports")
@click.argument("path")
def import_airports(path="tests/SeeYou.cup"):
    """Import airports from a ".cup" file"""

    print("Import airports from '{}'...".format(path))
    airports = get_airports(path)
    db.session.bulk_save_objects(airports)
    db.session.commit()
    db.session.execute("UPDATE airports SET border = ST_Expand(location, 0.05)")
    db.session.commit()
    print("Imported {} airports.".format(len(airports)))


@user_cli.command("update_country_codes")
def update_country_codes():
    """Update country codes of all receivers."""

    update_country_code(session=db.session)
