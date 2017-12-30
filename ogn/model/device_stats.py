from sqlalchemy import Column, Integer, Date, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class DeviceStats(Base):
    __tablename__ = "device_stats"

    id = Column(Integer, primary_key=True)

    date = Column(Date)
    receiver_count = Column(Integer)
    aircraft_beacon_count = Column(Integer)
    max_altitude = Column(Float)

    # Relations
    device_id = Column(Integer, ForeignKey('device.id', ondelete='SET NULL'), index=True)
    device = relationship('Device', foreign_keys=[device_id], backref='stats')

    def __repr__(self):
        return "<DeviceStats: %s,%s,%s,%s>" % (
            self.date,
            self.receiver_count,
            self.aircraft_beacon_count,
            self.max_altitude)
