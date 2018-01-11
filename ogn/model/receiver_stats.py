from sqlalchemy import Column, Integer, Date, Float, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class ReceiverStats(Base):
    __tablename__ = "receiver_stats"

    id = Column(Integer, primary_key=True)

    date = Column(Date)
    aircraft_beacon_count = Column(Integer)
    receiver_beacon_count = Column(Integer)
    aircraft_count = Column(Integer)
    max_distance = Column(Float)

    # Relations
    receiver_id = Column(Integer, ForeignKey('receivers.id', ondelete='SET NULL'), index=True)
    receiver = relationship('Receiver', foreign_keys=[receiver_id], backref='stats')
