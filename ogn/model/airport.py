from geoalchemy2.types import Geometry
from sqlalchemy import Column, String, Integer, Float, SmallInteger

from ogn import db


class Airport(db.Model):
    __tablename__ = "airports"

    id = Column(Integer, primary_key=True)

    location_wkt = Column('location', Geometry('POINT', srid=4326))
    altitude = Column(Float(precision=2))

    name = Column(String, index=True)
    code = Column(String(6))
    country_code = Column(String(2))
    style = Column(SmallInteger)
    description = Column(String)
    runway_direction = Column(SmallInteger)
    runway_length = Column(SmallInteger)
    frequency = Column(Float(precision=2))

    border = Column('border', Geometry('POLYGON', srid=4326))

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
