from sqlalchemy import Integer, DateTime, Interval, Column, ForeignKey, case, null
from sqlalchemy.orm import relationship

from .base import Base
from sqlalchemy.ext.hybrid import hybrid_property


class Logbook(Base):
    __tablename__ = 'logbook'

    id = Column(Integer, primary_key=True)

    reftime = Column(DateTime, index=True)
    takeoff_timestamp = Column(DateTime)
    takeoff_track = Column(Integer)
    landing_timestamp = Column(DateTime)
    landing_track = Column(Integer)
    max_altitude = Column(Integer)

    # Relations
    takeoff_airport_id = Column(Integer, ForeignKey('airport.id', ondelete='CASCADE'), index=True)
    takeoff_airport = relationship('Airport', foreign_keys=[takeoff_airport_id])

    landing_airport_id = Column(Integer, ForeignKey('airport.id', ondelete='CASCADE'), index=True)
    landing_airport = relationship('Airport', foreign_keys=[landing_airport_id])

    device_id = Column(Integer, ForeignKey('device.id', ondelete='CASCADE'), index=True)
    device = relationship('Device', foreign_keys=[device_id])

    @hybrid_property
    def duration(self):
        return None if (self.landing_timestamp is None or self.takeoff_timestamp is None) else self.landing_timestamp - self.takeoff_timestamp

    @duration.expression
    def duration(cls):
        return case({False: None, True: cls.landing_timestamp - cls.takeoff_timestamp}, cls.landing_timestamp != null() and cls.takeoff_timestamp != null())
