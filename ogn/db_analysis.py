from datetime import datetime, timedelta

from sqlalchemy.sql import func
from sqlalchemy import distinct, and_

from ogn.db import session
from ogn.model import Receiver

back_24h = datetime.utcnow() - timedelta(days=1)
receiver_messages_per_24h = 24*60 / 5


def get_receiver_info():
    sq = session.query(distinct(Receiver.name).label('name'), func.max(Receiver.timestamp).label('lastseen'), func.count(Receiver.name).label('messages_count')).\
        filter(Receiver.timestamp > back_24h).\
        group_by(Receiver.name).\
        subquery()

    query = session.query(Receiver, sq.c.messages_count).\
        filter(and_(Receiver.name == sq.c.name, Receiver.timestamp == sq.c.lastseen)).\
        order_by(Receiver.name)

    print('--- Receivers ---')
    for [receiver, messages_count] in query.all():
        print('%9s: %3d%% avail, %s, %s ' % (receiver.name, 100.0*float(messages_count/receiver_messages_per_24h), receiver.version, receiver.platform))


def get_software_stats():
    sq = session.query(Receiver.name, func.max(Receiver.timestamp).label('lastseen')).\
        filter(Receiver.timestamp > back_24h).\
        group_by(Receiver.name).\
        subquery()

    versions = session.query(distinct(Receiver.version), func.count(Receiver.version)).\
        filter(and_(Receiver.name == sq.c.name, Receiver.timestamp == sq.c.lastseen)).\
        group_by(Receiver.version).\
        order_by(Receiver.version)

    print('\n--- Versions ---')
    for [version, count] in versions.all():
        print('%5s: %s' % (version, count))


def get_hardware_stats():
    sq = session.query(Receiver.name, func.max(Receiver.timestamp).label('lastseen')).\
        filter(Receiver.timestamp > back_24h).\
        group_by(Receiver.name).\
        subquery()

    platforms = session.query(distinct(Receiver.platform), func.count(Receiver.platform)).\
        filter(and_(Receiver.name == sq.c.name, Receiver.timestamp == sq.c.lastseen)).\
        group_by(Receiver.platform).\
        order_by(Receiver.platform)

    print('\n--- Platforms ---')
    for [platform, count] in platforms.all():
        print('%7s: %s' % (platform, count))


if __name__ == '__main__':
    get_receiver_info()
    get_software_stats()
    get_hardware_stats()
