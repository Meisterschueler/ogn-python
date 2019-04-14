from flask.cli import AppGroup
import click

from datetime import datetime
from tqdm import tqdm

from ogn_python.commands.database import get_database_days

from ogn_python.collect.stats import create_device_stats, create_receiver_stats, create_relation_stats, create_country_stats,\
    update_qualities, update_receivers as update_receivers_command, update_devices as update_devices_command,\
    update_device_stats_jumps

from ogn_python.collect.ognrange import update_entries as update_receiver_coverages

from ogn_python import db


user_cli = AppGroup('stats')
user_cli.help = "Handling of statistical data."


@user_cli.command('create')
@click.argument('start')
@click.argument('end')
def create(start, end):
    """Create DeviceStats, ReceiverStats and RelationStats."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, '%Y-%m-%d'))
        result = create_device_stats(session=db.session, date=single_date)
        result = update_device_stats_jumps(session=db.session, date=single_date)
        result = create_receiver_stats(session=db.session, date=single_date)
        result = create_relation_stats(session=db.session, date=single_date)
        result = update_qualities(session=db.session, date=single_date)

@user_cli.command('create_country')
@click.argument('start')
@click.argument('end')
def create_country(start, end):
    """Create CountryStats."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, '%Y-%m-%d'))
        result = create_country_stats(session=db.session, date=single_date)

from ogn_python.model import *
@user_cli.command('update_devices_name')
def update_devices_name():
    """Update Devices name."""

    device_ids = db.session.query(Device.id).all()

    for device_id in tqdm(device_ids):
        db.session.execute("update devices d set name = sq.name from ( select * from aircraft_beacons ab where ab.device_id = {} limit 1) sq where d.id = sq.device_id and d.name is null or d.name = 'ICA3D3CC4';".format(device_id[0]))
        db.session.commit()


@user_cli.command('update_receivers')
def update_receivers():
    """Update receivers with data from stats."""

    result = update_receivers_command(session=db.session)
    print(result)


@user_cli.command('update_devices')
def update_devices():
    """Update devices with data from stats."""

    result = update_devices_command(session=db.session)
    print(result)


@user_cli.command('update_mgrs')
@click.argument('start')
@click.argument('end')
def update_mgrs(start, end):
    """Create location_mgrs_short."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        datestr = datetime.strftime(single_date, '%Y-%m-%d')
        pbar.set_description(datestr)
        for pbar2 in tqdm(["{:02d}:{:02d}".format(hh, mm) for hh in range(0, 24) for mm in range(0, 60)]):
            sql = """
                UPDATE aircraft_beacons
                SET location_mgrs_short = left(location_mgrs, 5) || substring(location_mgrs, 6, 2) || substring(location_mgrs, 11, 2)
                WHERE timestamp BETWEEN '{0} {1}:00' and '{0} {1}:59' AND location_mgrs_short IS NULL;
            """.format(datestr, pbar2)

            #print(sql)
            db.session.execute(sql)
            db.session.commit()


@user_cli.command('create_ognrange')
@click.argument('start')
@click.argument('end')
def create_ognrange(start=None, end=None):
    """Create receiver coverage stats for Melissas ognrange."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, '%Y-%m-%d'))
        result = update_receiver_coverages(session=db.session, date=single_date)
