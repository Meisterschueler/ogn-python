from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship

from .base import Base
from .geo import Location


class Receiver(Base):
    __tablename__ = "receiver"

    id = Column(Integer, primary_key=True)

    location_wkt = Column('location', Geometry('POINT', srid=4326))
    altitude = Column(Integer)

    name = Column(String(9))
    firstseen = Column(DateTime, index=True)
    lastseen = Column(DateTime, index=True)
    country_code = Column(String(2))
    version = Column(String)
    platform = Column(String)

    # Relations
    aircraft_beacons = relationship('AircraftBeacon')
    receiver_beacons = relationship('ReceiverBeacon')

    @property
    def location(self):
        if self.location_wkt is None:
            return None

        coords = to_shape(self.location_wkt)
        return Location(lat=coords.y, lon=coords.x)
