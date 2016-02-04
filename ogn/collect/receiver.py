from sqlalchemy.sql import func, null
from sqlalchemy.sql.functions import coalesce
from sqlalchemy import and_, or_

from celery.utils.log import get_task_logger

from ogn.model import Receiver, ReceiverBeacon
from ogn.utils import get_country_code
from ogn.collect.celery import app

logger = get_task_logger(__name__)


@app.task
def update_receivers():
    """Update the receiver table."""
    # get current receiver data
    last_entry_sq = app.session.query(coalesce(func.max(Receiver.lastseen), '2015-01-01 00:00:00').label('last_entry')) \
                               .subquery()

    last_receiver_beacon_sq = app.session.query(ReceiverBeacon.name, func.min(ReceiverBeacon.timestamp).label('firstseen'), func.max(ReceiverBeacon.timestamp).label('lastseen')) \
                                 .filter(ReceiverBeacon.timestamp >= last_entry_sq.c.last_entry) \
                                 .group_by(ReceiverBeacon.name) \
                                 .subquery()

    # update existing receivers
    sq = app.session.query(ReceiverBeacon.name, ReceiverBeacon.latitude, ReceiverBeacon.longitude, ReceiverBeacon.altitude, last_receiver_beacon_sq.c.firstseen, last_receiver_beacon_sq.c.lastseen, ReceiverBeacon.version, ReceiverBeacon.platform) \
            .filter(and_(ReceiverBeacon.name == last_receiver_beacon_sq.c.name, ReceiverBeacon.timestamp == last_receiver_beacon_sq.c.lastseen)) \
            .subquery()

    # -set country code to None if lat or lon changed
    upd = app.session.query(Receiver) \
                     .filter(and_(Receiver.name == sq.c.name,
                                  or_(Receiver.latitude != sq.c.latitude,
                                      Receiver.longitude != sq.c.longitude)
                                  )
                             ) \
                     .update({"latitude": sq.c.latitude,
                              "longitude": sq.c.longitude,
                              "country_code": None})

    logger.info("Count of receivers who changed lat or lon: {}".format(upd))
    app.session.commit()

    # -update lastseen of known receivers
    upd = app.session.query(Receiver) \
                     .filter(Receiver.name == sq.c.name) \
                     .update({"altitude": sq.c.altitude,
                              "lastseen": sq.c.lastseen,
                              "version": sq.c.version,
                              "platform": sq.c.platform})

    logger.info("Count of receivers who where updated: {}".format(upd))

    # add new receivers
    empty_sq = app.session.query(ReceiverBeacon.name, ReceiverBeacon.latitude, ReceiverBeacon.longitude, ReceiverBeacon.altitude, last_receiver_beacon_sq.c.firstseen, last_receiver_beacon_sq.c.lastseen, ReceiverBeacon.version, ReceiverBeacon.platform) \
                          .filter(and_(ReceiverBeacon.name == last_receiver_beacon_sq.c.name,
                                       ReceiverBeacon.timestamp == last_receiver_beacon_sq.c.lastseen)) \
                          .outerjoin(Receiver, Receiver.name == ReceiverBeacon.name) \
                          .filter(Receiver.name == null()) \
                          .order_by(ReceiverBeacon.name)

    for receiver_beacon in empty_sq.all():
        receiver = Receiver()
        receiver.name = receiver_beacon.name
        receiver.latitude = receiver_beacon.latitude
        receiver.longitude = receiver_beacon.longitude
        receiver.altitude = receiver_beacon.altitude
        receiver.firstseen = receiver_beacon.firstseen
        receiver.lastseen = receiver_beacon.lastseen
        receiver.version = receiver_beacon.version
        receiver.platform = receiver_beacon.platform

        app.session.add(receiver)
        logger.info("{} added".format(receiver.name))

    app.session.commit()

    # update country code if None
    unknown_country_query = app.session.query(Receiver) \
                                       .filter(Receiver.country_code == null()) \
                                       .order_by(Receiver.name)

    for receiver in unknown_country_query.all():
        receiver.country_code = get_country_code(receiver.latitude, receiver.longitude)
        if receiver.country_code is not None:
            logger.info("Updated country_code for {} to {}".format(receiver.name, receiver.country_code))

    app.session.commit()
