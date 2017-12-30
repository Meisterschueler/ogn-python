from geoalchemy2.types import Geometry
from sqlalchemy import Column, String, Integer, Float, SmallInteger
from sqlalchemy.orm import relationship

from .base import Base


class Airport(Base):
    __tablename__ = "airport"

    id = Column(Integer, primary_key=True)

    location_wkt = Column('location', Geometry('POINT', srid=4326))
    altitude = Column(Integer)

    name = Column(String, index=True)
    code = Column(String(6))
    country_code = Column(String(2))
    style = Column(SmallInteger)
    description = Column(String)
    runway_direction = Column(Integer)
    runway_length = Column(Integer)
    frequency = Column(Float)

    def __repr__(self):
        return "<Airport %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,% s>" % (
            self.name,
            self.code,
            self.country_code,
            self.style,
            self.description,
            self.location_wkt.latitude if self.location_wkt else None,
            self.location_wkt.longitude if self.location_wkt else None,
            self.altitude,
            self.runway_direction,
            self.runway_length,
            self.frequency)
