from sqlalchemy import Column, Integer, SmallInteger, Date, Float, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from geoalchemy2.types import Geometry

from .base import Base


class ReceiverStats(Base):
    __tablename__ = "receiver_stats"

    id = Column(Integer, primary_key=True)

    date = Column(Date)

    # Statistic data
    aircraft_beacon_count = Column(Integer)
    aircraft_count = Column(SmallInteger)
    max_distance = Column(Float)
    firstseen = Column(DateTime, index=True)
    lastseen = Column(DateTime, index=True)
    location_wkt = Column('location', Geometry('POINT', srid=4326))
    altitude = Column(Float(precision=2))
    version = Column(String)
    platform = Column(String)

    # Relations
    receiver_id = Column(Integer, ForeignKey('receivers.id', ondelete='SET NULL'), index=True)
    receiver = relationship('Receiver', foreign_keys=[receiver_id], backref='stats')
