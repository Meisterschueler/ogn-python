from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry
from sqlalchemy import Column, Float, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref

from .geo import Location

from ogn import db


class Receiver(db.Model):
    __tablename__ = "receivers"

    id = Column(Integer, primary_key=True)

    location_wkt = Column('location', Geometry('POINT', srid=4326))
    altitude = Column(Float(precision=2))

    name = Column(String(9), index=True)
    firstseen = Column(DateTime, index=True)
    lastseen = Column(DateTime, index=True)
    version = Column(String)
    platform = Column(String)

    # Relations
    country_id = Column(Integer, ForeignKey('countries.gid', ondelete='SET NULL'), index=True)
    country = relationship('Country', foreign_keys=[country_id], backref=backref('receivers', order_by='Receiver.name.asc()'))

    @property
    def location(self):
        if self.location_wkt is None:
            return None

        coords = to_shape(self.location_wkt)
        return Location(lat=coords.y, lon=coords.x)
