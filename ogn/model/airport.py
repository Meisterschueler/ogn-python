from sqlalchemy import Column, String, Integer, Float, SmallInteger
from sqlalchemy.orm import relationship
from geoalchemy2.types import Geometry

from .base import Base


class Airport(Base):
    __tablename__ = "airport"

    id = Column(Integer, primary_key=True)

    location_wkt = Column('location', Geometry('POINT', srid=4326))
    altitude = Column(Integer)

    name = Column(String, index=True)
    code = Column(String(5))
    country_code = Column(String(2))
    style = Column(SmallInteger)
    description = Column(String)
    runway_direction = Column(Integer)
    runway_length = Column(Integer)
    frequency = Column(Float)

    # Relations
    takeoff_landings = relationship('TakeoffLanding')

    def __repr__(self):
        return "<Airport %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,% s>" % (
            self.name,
            self.code,
            self.country_code,
            self.style,
            self.description,
            self.latitude,
            self.longitude,
            self.altitude,
            self.runway_direction,
            self.runway_length,
            self.frequency)
