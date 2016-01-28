from sqlalchemy import create_engine, and_, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import null

from ogn.model import AircraftBeacon, ReceiverBeacon
from ogn.utils import wgs84_to_sphere

engine = create_engine('sqlite:///beacons.db', echo=False)

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
        [radius, theta, phi] = wgs84_to_sphere(last_receiver_beacon,
                                               aircraft_beacon)
        aircraft_beacon.radius = radius
        aircraft_beacon.theta = theta
        aircraft_beacon.phi = phi
    session.commit()
