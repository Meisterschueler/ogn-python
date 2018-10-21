from sqlalchemy import Column, Integer, SmallInteger, Date, Float, ForeignKey, DateTime, String, Index
from sqlalchemy.orm import relationship, backref
from geoalchemy2.types import Geometry

from .base import Base


class ReceiverStats(Base):
    __tablename__ = "receiver_stats"

    id = Column(Integer, primary_key=True)

    date = Column(Date)

    # Static data
    firstseen = Column(DateTime, index=True)
    lastseen = Column(DateTime, index=True)
    location_wkt = Column('location', Geometry('POINT', srid=4326))
    altitude = Column(Float(precision=2))
    version = Column(String)
    platform = Column(String)

    # Statistic data
    aircraft_beacon_count = Column(Integer)
    aircraft_count = Column(SmallInteger)
    max_distance = Column(Float)
    quality = Column(Float(precision=2))
    
    # Relation statistic data
    quality_offset = Column(Float(precision=2))
    
    # Ranking data
    aircraft_beacon_count_ranking_worldwide = Column(SmallInteger)
    aircraft_beacon_count_ranking_country = Column(SmallInteger)
    aircraft_count_ranking_worldwide = Column(SmallInteger)
    aircraft_count_ranking_country = Column(SmallInteger)
    max_distance_ranking_worldwide = Column(SmallInteger)
    max_distance_ranking_country = Column(SmallInteger)
    quality_ranking_worldwide = Column(Integer)
    quality_ranking_country = Column(Integer)

    # Relations
    receiver_id = Column(Integer, ForeignKey('receivers.id', ondelete='SET NULL'), index=True)
    receiver = relationship('Receiver', foreign_keys=[receiver_id], backref=backref('stats', order_by='ReceiverStats.date.asc()'))

Index('ix_receiver_stats_date_receiver_id', ReceiverStats.date, ReceiverStats.receiver_id)