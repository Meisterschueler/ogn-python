from datetime import datetime
from tqdm import tqdm
from manager import Manager
from ogn.commands.dbutils import session
from ogn.commands.database import get_database_days

from ogn.collect.stats import create_device_stats, create_receiver_stats, create_relation_stats,\
    update_qualities, update_receivers as update_receivers_command, update_devices as update_devices_command,\
    update_device_stats_jumps

manager = Manager()


@manager.command
def create(start=None, end=None):
    """Create DeviceStats, ReceiverStats and RelationStats."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, '%Y-%m-%d'))
        result = create_device_stats(session=session, date=single_date)
        result = update_device_stats_jumps(session=session, date=single_date)
        result = create_receiver_stats(session=session, date=single_date)
        result = create_relation_stats(session=session, date=single_date)
        result = update_qualities(session=session, date=single_date)


@manager.command
def update_receivers():
    """Update receivers with data from stats."""

    result = update_receivers_command(session=session)
    print(result)


@manager.command
def update_devices():
    """Update devices with data from stats."""

    result = update_devices_command(session=session)
    print(result)
