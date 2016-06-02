from sqlalchemy import Boolean, Column, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2.shape import to_shape

from .base import Base
from .geo import Location


class TakeoffLanding(Base):
    __tablename__ = 'takeoff_landing'

    id = Column(Integer, primary_key=True)

    altitude = Column(Integer)
    timestamp = Column(DateTime, index=True)
    track = Column(Integer)
    ground_speed = Column(Float)

    is_takeoff = Column(Boolean)

    # Relations
    airport_id = Column(Integer, ForeignKey('airport.id', ondelete='SET NULL'), index=True)
    airport = relationship('Airport', foreign_keys=[airport_id])

    device_id = Column(Integer, ForeignKey('device.id', ondelete='SET NULL'), index=True)
    device = relationship('Device', foreign_keys=[device_id])

    @property
    def location(self):
        if self.location_wkt is None:
            return None

        coords = to_shape(self.location_wkt)
        return Location(lat=coords.y, lon=coords.x)
