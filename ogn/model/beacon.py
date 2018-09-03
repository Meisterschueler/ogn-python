from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry
from sqlalchemy import Column, String, Integer, SmallInteger, Float, DateTime
from sqlalchemy.ext.declarative import AbstractConcreteBase

from .base import Base
from .geo import Location


class Beacon(AbstractConcreteBase, Base):
    id = Column(Integer, primary_key=True)

    # APRS data
    location_wkt = Column('location', Geometry('POINT', srid=4326))
    altitude = Column(Float(precision=2))

    name = Column(String)
    dstcall = Column(String)
    relay = Column(String)
    receiver_name = Column(String(9))
    timestamp = Column(DateTime, index=True)
    symboltable = None
    symbolcode = None
    track = Column(SmallInteger)
    ground_speed = Column(Float(precision=2))
    comment = None

    # Type information
    beacon_type = None
    aprs_type = None

    # Debug information
    raw_message = None #Column(String)
    reference_timestamp = None #Column(DateTime, index=True)

    @property
    def location(self):
        if self.location_wkt is None:
            return None

        coords = to_shape(self.location_wkt)
        return Location(lat=coords.y, lon=coords.x)
