from math import atan2, pi, sqrt

from sqlalchemy import and_, desc, distinct
from sqlalchemy.sql import null

from celery import group
from celery.utils.log import get_task_logger
from ogn.collect.celery import app

from ogn.model import AircraftBeacon, ReceiverBeacon
from ogn.utils import haversine_distance

logger = get_task_logger(__name__)


@app.task
def update_beacon_receiver_distance(name):
    """
    Calculate the distance between the receiver and its received aircrafts
    and write this data into each aircraft_beacon.
    """

    last_receiver_beacon = app.session.query(ReceiverBeacon) \
        .filter(ReceiverBeacon.name == name) \
        .order_by(desc(ReceiverBeacon.timestamp)) \
        .first()

    if (last_receiver_beacon is None):
        return

    aircraft_beacons_query = app.session.query(AircraftBeacon) \
        .filter(and_(AircraftBeacon.timestamp > last_receiver_beacon.timestamp,
                     AircraftBeacon.receiver_name == name,
                     AircraftBeacon.radius == null()))

    for aircraft_beacon in aircraft_beacons_query.all():
        location0 = (last_receiver_beacon.latitude, last_receiver_beacon.longitude)
        location1 = (aircraft_beacon.latitude, aircraft_beacon.longitude)
        alt0 = last_receiver_beacon.altitude
        alt1 = aircraft_beacon.altitude

        (flat_distance, phi) = haversine_distance(location0, location1)
        theta = atan2(alt1 - alt0, flat_distance) * 180 / pi
        distance = sqrt(flat_distance**2 + (alt1 - alt0)**2)

        aircraft_beacon.radius = distance
        aircraft_beacon.theta = theta
        aircraft_beacon.phi = phi

    app.session.commit()
    logger.warning("Updated receiver {}.".format(name))


@app.task
def update_beacon_receiver_distance_all():
    group(update_beacon_receiver_distance(receiver.name)
          for receiver in app.session.query(distinct(ReceiverBeacon.name).label('name')))
