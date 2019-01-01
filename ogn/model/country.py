from geoalchemy2.types import Geometry
from sqlalchemy import Column, String, Integer, Float, SmallInteger, BigInteger

from .base import Base


class Country(Base):
    __tablename__ = "countries"

    gid = Column(Integer, primary_key=True)

    fips = Column(String(2))
    iso2 = Column(String(2))
    iso3 = Column(String(3))

    un = Column(SmallInteger)
    name = Column(String(50))
    area = Column(Integer)
    pop2005 = Column(BigInteger)
    region = Column(SmallInteger)
    subregion = Column(SmallInteger)
    lon = Column(Float)
    lat = Column(Float)

    geom = Column('geom', Geometry('MULTIPOLYGON', srid=4326))

    def __repr__(self):
        return "<Country %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,% s>" % (
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
