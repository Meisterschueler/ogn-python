from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry
from sqlalchemy import Column, Float, String, Integer, DateTime
from sqlalchemy.orm import relationship

from .base import Base
from .geo import Location


class Receiver(Base):
    __tablename__ = "receivers"

    id = Column(Integer, primary_key=True)

    location_wkt = Column('location', Geometry('POINT', srid=4326))
    altitude = Column(Float(precision=2))

    name = Column(String(9))
    firstseen = Column(DateTime, index=True)
    lastseen = Column(DateTime, index=True)
    country_code = Column(String(2))
    version = Column(String)
    platform = Column(String)

    @property
    def location(self):
        if self.location_wkt is None:
            return None

        coords = to_shape(self.location_wkt)
        return Location(lat=coords.y, lon=coords.x)
