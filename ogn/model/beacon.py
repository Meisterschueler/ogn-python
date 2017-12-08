from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry
from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.ext.declarative import AbstractConcreteBase

from .base import Base
from .geo import Location


class Beacon(AbstractConcreteBase, Base):
    id = Column(Integer, primary_key=True)

    # APRS data
    location_wkt = Column('location', Geometry('POINT', srid=4326))
    altitude = Column(Integer)

    name = Column(String)
    receiver_name = Column(String(9))
    dstcall = None
    timestamp = Column(DateTime, index=True)
    symboltable = None
    symbolcode = None
    track = Column(Integer)
    ground_speed = Column(Float)
    comment = None

    relay = None
    beacon_type = None
    aprs_type = None

    @property
    def location(self):
        if self.location_wkt is None:
            return None

        coords = to_shape(self.location_wkt)
        return Location(lat=coords.y, lon=coords.x)
