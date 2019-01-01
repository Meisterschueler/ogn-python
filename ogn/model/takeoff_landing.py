from sqlalchemy import Boolean, Column, Integer, SmallInteger, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class TakeoffLanding(Base):
    __tablename__ = 'takeoff_landings'

    device_id = Column(Integer, ForeignKey('devices.id', ondelete='SET NULL'), primary_key=True)
    airport_id = Column(Integer, ForeignKey('airports.id', ondelete='SET NULL'), primary_key=True)
    timestamp = Column(DateTime, primary_key=True)

    is_takeoff = Column(Boolean)
    track = Column(SmallInteger)

    # Relations
    airport = relationship('Airport', foreign_keys=[airport_id], backref='takeoff_landings')
    device = relationship('Device', foreign_keys=[device_id], backref='takeoff_landings')
