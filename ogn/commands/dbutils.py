import os
import importlib

from sqlalchemy import create_engine, and_, desc
from sqlalchemy.sql import null
from sqlalchemy.orm import sessionmaker

from ogn.model import AircraftBeacon, ReceiverBeacon
from ogn.utils import haversine_distance


os.environ.setdefault('OGN_CONFIG_MODULE', 'config.default')

config = importlib.import_module(os.environ['OGN_CONFIG_MODULE'])
engine = create_engine(config.SQLALCHEMY_DATABASE_URI, echo=False)

Session = sessionmaker(bind=engine)
session = Session()


def update_receiver_childs(name):
    last_receiver_beacon = session.query(ReceiverBeacon) \
        .filter(ReceiverBeacon.name == name) \
        .order_by(desc(ReceiverBeacon.timestamp)) \
        .first()

    if (last_receiver_beacon is None):
        return

    aircraft_beacons_query = session.query(AircraftBeacon) \
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
    session.commit()
