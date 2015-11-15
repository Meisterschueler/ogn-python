from datetime import datetime, timedelta

from sqlalchemy.sql import func
from sqlalchemy import distinct, and_

from ogn.db import session
from ogn.model import ReceiverBeacon
from ogn.model.receiver_device import ReceiverDevice

back_24h = datetime.utcnow() - timedelta(days=1)
receiver_messages_per_24h = 24*60 / 5


def get_receiver_info():
    sq = session.query(distinct(ReceiverBeacon.name).label('name'), func.max(ReceiverBeacon.timestamp).label('lastseen'), func.count(ReceiverBeacon.name).label('messages_count')).\
        filter(ReceiverBeacon.timestamp > back_24h).\
        group_by(ReceiverBeacon.name).\
        subquery()

    query = session.query(ReceiverDevice, sq.c.messages_count).\
        filter(ReceiverDevice.name == sq.c.name).\
        order_by(ReceiverDevice.name)

    print('--- Receivers ---')
    for [receiver, messages_count] in query.all():
        print('%9s (%2s): %3d%% avail, %s, %s ' % (receiver.name, receiver.country_code, 100.0*float(messages_count/receiver_messages_per_24h), receiver.version, receiver.platform))


def get_software_stats():
    sq = session.query(ReceiverBeacon.name, func.max(ReceiverBeacon.timestamp).label('lastseen')).\
        filter(ReceiverBeacon.timestamp > back_24h).\
        group_by(ReceiverBeacon.name).\
        subquery()

    versions = session.query(distinct(ReceiverBeacon.version), func.count(ReceiverBeacon.version)).\
        filter(and_(ReceiverBeacon.name == sq.c.name, ReceiverBeacon.timestamp == sq.c.lastseen)).\
        group_by(ReceiverBeacon.version).\
        order_by(ReceiverBeacon.version)

    print('\n--- Versions ---')
    for [version, count] in versions.all():
        print('%5s: %s' % (version, count))


def get_hardware_stats():
    sq = session.query(ReceiverBeacon.name, func.max(ReceiverBeacon.timestamp).label('lastseen')).\
        filter(ReceiverBeacon.timestamp > back_24h).\
        group_by(ReceiverBeacon.name).\
        subquery()

    platforms = session.query(distinct(ReceiverBeacon.platform), func.count(ReceiverBeacon.platform)).\
        filter(and_(ReceiverBeacon.name == sq.c.name, ReceiverBeacon.timestamp == sq.c.lastseen)).\
        group_by(ReceiverBeacon.platform).\
        order_by(ReceiverBeacon.platform)

    print('\n--- Platforms ---')
    for [platform, count] in platforms.all():
        print('%7s: %s' % (platform, count))


if __name__ == '__main__':
    get_receiver_info()
    get_software_stats()
    get_hardware_stats()
