from sqlalchemy import Boolean, Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class TakeoffLanding(Base):
    __tablename__ = 'takeoff_landing'

    id = Column(Integer, primary_key=True)

    is_takeoff = Column(Boolean)
    timestamp = Column(DateTime, index=True)
    track = Column(Integer)

    # Relations
    airport_id = Column(Integer, ForeignKey('airport.id', ondelete='SET NULL'), index=True)
    airport = relationship('Airport', foreign_keys=[airport_id])

    device_id = Column(Integer, ForeignKey('device.id', ondelete='SET NULL'), index=True)
    device = relationship('Device', foreign_keys=[device_id])

    def __init__(self, is_takeoff, timestamp, airport_id, device_id):
        self.is_takeoff = is_takeoff
        self.timestamp = timestamp
        self.airport_id = airport_id
        self.device_id = device_id
