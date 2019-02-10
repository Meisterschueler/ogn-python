from flask.cli import AppGroup
import click

from datetime import datetime
from tqdm import tqdm

from ogn_python.commands.database import get_database_days

from ogn_python.collect.stats import create_device_stats, create_receiver_stats, create_relation_stats,\
    update_qualities, update_receivers as update_receivers_command, update_devices as update_devices_command,\
    update_device_stats_jumps

from ogn_python.collect.ognrange import create_receiver_coverage

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


@user_cli.command('create_ognrange')
@click.argument('start')
@click.argument('end')
def create_ognrange(start=None, end=None):
    """Create stats for Melissas ognrange."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, '%Y-%m-%d'))
        result = create_receiver_coverage(session=db.session, date=single_date)
