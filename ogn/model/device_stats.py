from sqlalchemy import Column, Integer, Date, DateTime, Float, ForeignKey, SmallInteger, Boolean, String, Index
from sqlalchemy.orm import relationship, backref

from .base import Base


class DeviceStats(Base):
    __tablename__ = "device_stats"

    id = Column(Integer, primary_key=True)

    date = Column(Date)

    # Static data
    firstseen = Column(DateTime)
    lastseen = Column(DateTime)
    aircraft_type = Column(SmallInteger)
    stealth = Column(Boolean)
    software_version = Column(Float(precision=2))
    hardware_version = Column(SmallInteger)
    real_address = Column(String(6))

    # Statistic data
    max_altitude = Column(Float(precision=2))
    receiver_count = Column(SmallInteger)
    aircraft_beacon_count = Column(Integer)
    jumps = Column(SmallInteger)
    ambiguous = Column(Boolean)
    quality = Column(Float(precision=2))
    
    # Relation statistic data
    quality_offset = Column(Float(precision=2))
    
    # Ranking data
    max_altitude_ranking_worldwide = Column(Integer)
    max_altitude_ranking_country = Column(Integer)
    receiver_count_ranking_worldwide = Column(Integer)
    receiver_count_ranking_country = Column(Integer)
    aircraft_beacon_count_ranking_worldwide = Column(Integer)
    aircraft_beacon_count_ranking_country = Column(Integer)
    quality_ranking_worldwide = Column(Integer)
    quality_ranking_country = Column(Integer)

    # Relations
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='SET NULL'), index=True)
    device = relationship('Device', foreign_keys=[device_id], backref=backref('stats', order_by='DeviceStats.date.asc()'))
    
    def __repr__(self):
        return "<DeviceStats: %s,%s,%s,%s>" % (
            self.date,
            self.receiver_count,
            self.aircraft_beacon_count,
            self.max_altitude)

Index('ix_device_stats_date_device_id', DeviceStats.date, DeviceStats.device_id)