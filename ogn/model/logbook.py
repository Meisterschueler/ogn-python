from sqlalchemy import Integer, DateTime, Interval, Column, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Logbook(Base):
    __tablename__ = 'logbook'

    id = Column(Integer, primary_key=True)

    reftime = Column(DateTime, index=True)
    takeoff_timestamp = Column(DateTime)
    takeoff_track = Column(Integer)
    landing_timestamp = Column(DateTime)
    landing_track = Column(Integer)
    duration = Column(Interval)
    max_altitude = Column(Integer)

    # Relations
    takeoff_airport_id = Column(Integer, ForeignKey('airport.id', ondelete='CASCADE'), index=True)
    takeoff_airport = relationship('Airport', foreign_keys=[takeoff_airport_id])

    landing_airport_id = Column(Integer, ForeignKey('airport.id', ondelete='CASCADE'), index=True)
    landing_airport = relationship('Airport', foreign_keys=[landing_airport_id])

    device_id = Column(Integer, ForeignKey('device.id', ondelete='CASCADE'), index=True)
    device = relationship('Device', foreign_keys=[device_id])
