from datetime import datetime, timedelta
from sqlalchemy.sql import func
from sqlalchemy import distinct, and_

from ogn.model import ReceiverBeacon, Receiver
from ogn.commands.dbutils import session

from manager import Manager
manager = Manager()

receiver_beacons_per_day = 24 * 60 / 5


@manager.command
def list_all():
    """Show a list of all receivers."""
    timestamp_24h_ago = datetime.utcnow() - timedelta(days=1)

    sq = session.query(distinct(ReceiverBeacon.name).label('name'),
                       func.max(ReceiverBeacon.timestamp).label('lastseen'),
                       func.count(ReceiverBeacon.name).label('messages_count')) \
                .filter(ReceiverBeacon.timestamp > timestamp_24h_ago) \
                .group_by(ReceiverBeacon.name).subquery()

    query = session.query(Receiver, sq.c.messages_count).\
        filter(Receiver.name == sq.c.name).\
        order_by(Receiver.name)

    print('--- Receivers ---')
    for [receiver, messages_count] in query.all():
        print('%9s (%2s): %3d%% avail, %s, %s ' % (receiver.name,
                                                   receiver.country_code,
                                                   100.0 * float(messages_count / receiver_beacons_per_day),
                                                   receiver.version,
                                                   receiver.platform))


@manager.command
def software_stats():
    """Show some statistics of receiver software."""

    timestamp_24h_ago = datetime.utcnow() - timedelta(days=1)

    sq = session.query(ReceiverBeacon.name, func.max(ReceiverBeacon.timestamp).label('lastseen')).\
        filter(ReceiverBeacon.timestamp > timestamp_24h_ago).\
        group_by(ReceiverBeacon.name).\
        subquery()

    versions = session.query(distinct(ReceiverBeacon.version), func.count(ReceiverBeacon.version)).\
        filter(and_(ReceiverBeacon.name == sq.c.name, ReceiverBeacon.timestamp == sq.c.lastseen)).\
        group_by(ReceiverBeacon.version).\
        order_by(ReceiverBeacon.version)

    print('--- Versions ---')
    for [version, count] in versions.all():
        print('%5s: %s' % (version, count))


@manager.command
def hardware_stats():
    """Show some statistics of receiver hardware."""

    timestamp_24h_ago = datetime.utcnow() - timedelta(days=1)

    sq = session.query(ReceiverBeacon.name, func.max(ReceiverBeacon.timestamp).label('lastseen')).\
        filter(ReceiverBeacon.timestamp > timestamp_24h_ago).\
        group_by(ReceiverBeacon.name).\
        subquery()

    platforms = session.query(distinct(ReceiverBeacon.platform), func.count(ReceiverBeacon.platform)).\
        filter(and_(ReceiverBeacon.name == sq.c.name, ReceiverBeacon.timestamp == sq.c.lastseen)).\
        group_by(ReceiverBeacon.platform).\
        order_by(ReceiverBeacon.platform)

    print('--- Platforms ---')
    for [platform, count] in platforms.all():
        print('%7s: %s' % (platform, count))
