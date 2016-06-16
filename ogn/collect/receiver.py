from sqlalchemy.sql import func, null
from sqlalchemy.sql.functions import coalesce
from sqlalchemy import and_, not_, or_

from celery.utils.log import get_task_logger

from ogn.model import Receiver, ReceiverBeacon
from ogn.utils import get_country_code
from ogn.collect.celery import app

logger = get_task_logger(__name__)


@app.task
def update_receivers():
    """Update the receiver table."""
    # get the timestamp of last update
    last_update_query = app.session.query(coalesce(func.max(Receiver.lastseen), '2015-01-01 00:00:00').label('last_entry'))
    last_update = last_update_query.one().last_entry

    # get last receiver beacons since last update
    last_receiver_beacon_sq = app.session.query(ReceiverBeacon.name,
                                                func.max(ReceiverBeacon.timestamp).label('lastseen')) \
                                         .filter(ReceiverBeacon.timestamp >= last_update) \
                                         .group_by(ReceiverBeacon.name) \
                                         .subquery()

    # update receivers
    receivers_to_update = app.session.query(ReceiverBeacon.name,
                                            ReceiverBeacon.location_wkt,
                                            ReceiverBeacon.altitude,
                                            last_receiver_beacon_sq.columns.lastseen,
                                            ReceiverBeacon.version,
                                            ReceiverBeacon.platform) \
                                     .filter(and_(ReceiverBeacon.name == last_receiver_beacon_sq.columns.name,
                                                  ReceiverBeacon.timestamp == last_receiver_beacon_sq.columns.lastseen)) \
                                     .subquery()

    # ... set country code to None if lat or lon changed
    changed_count = app.session.query(Receiver) \
                       .filter(Receiver.name == receivers_to_update.columns.name) \
                       .filter(or_(not_(func.ST_Equals(Receiver.location_wkt, receivers_to_update.columns.location)),
                                   and_(Receiver.location_wkt == null(),
                                        receivers_to_update.columns.location != null()))) \
                       .update({"location_wkt": receivers_to_update.columns.location,
                                "country_code": null()},
                               synchronize_session=False)

    # ... and update altitude, lastseen, version and platform
    update_count = app.session.query(Receiver) \
                      .filter(Receiver.name == receivers_to_update.columns.name) \
                      .update({"altitude": receivers_to_update.columns.altitude,
                               "lastseen": receivers_to_update.columns.lastseen,
                               "version": receivers_to_update.columns.version,
                               "platform": receivers_to_update.columns.platform})

    # add new receivers
    empty_sq = app.session.query(ReceiverBeacon.name,
                                 ReceiverBeacon.location_wkt,
                                 ReceiverBeacon.altitude,
                                 last_receiver_beacon_sq.columns.lastseen,
                                 ReceiverBeacon.version, ReceiverBeacon.platform) \
                          .filter(and_(ReceiverBeacon.name == last_receiver_beacon_sq.columns.name,
                                       ReceiverBeacon.timestamp == last_receiver_beacon_sq.columns.lastseen)) \
                          .outerjoin(Receiver, Receiver.name == ReceiverBeacon.name) \
                          .filter(Receiver.name == null()) \
                          .order_by(ReceiverBeacon.name)

    for receiver_beacon in empty_sq.all():
        receiver = Receiver()
        receiver.name = receiver_beacon.name
        receiver.location_wkt = receiver_beacon.location_wkt
        receiver.altitude = receiver_beacon.altitude
        receiver.firstseen = None
        receiver.lastseen = receiver_beacon.lastseen
        receiver.version = receiver_beacon.version
        receiver.platform = receiver_beacon.platform

        app.session.add(receiver)
        logger.info("{} added".format(receiver.name))

    # update firstseen if None
    firstseen_null_query = app.session.query(Receiver.name,
                                             func.min(ReceiverBeacon.timestamp).label('firstseen')) \
                                      .filter(Receiver.firstseen == null()) \
                                      .join(ReceiverBeacon, Receiver.name == ReceiverBeacon.name) \
                                      .group_by(Receiver.name) \
                                      .subquery()

    added_count = app.session.query(Receiver) \
        .filter(Receiver.name == firstseen_null_query.columns.name) \
        .update({'firstseen': firstseen_null_query.columns.firstseen})

    # update country code if None
    unknown_country_query = app.session.query(Receiver) \
                                       .filter(Receiver.country_code == null()) \
                                       .filter(Receiver.location_wkt != null()) \
                                       .order_by(Receiver.name)

    for receiver in unknown_country_query.all():
        location = receiver.location
        country_code = get_country_code(location.latitude, location.longitude)
        if country_code is not None:
            receiver.country_code = country_code
            logger.info("Updated country_code for {} to {}".format(receiver.name, receiver.country_code))

    logger.info("Added: {}, location changed: {}".format(added_count, changed_count))

    app.session.commit()

    return update_count
