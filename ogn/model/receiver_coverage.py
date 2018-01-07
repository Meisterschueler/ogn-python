from sqlalchemy import Column, String, Integer, Float, Date, ForeignKey, Index
from sqlalchemy.orm import relationship


from .base import Base


class ReceiverCoverage(Base):
    __tablename__ = "receiver_coverage"

    location_mgrs = Column(String(9), primary_key=True)
    receiver_id = Column(Integer, ForeignKey('receiver.id', ondelete='SET NULL'), primary_key=True)
    date = Column(Date, primary_key=True)

    max_signal_quality = Column(Float)
    max_altitude = Column(Integer)
    min_altitude = Column(Integer)
    aircraft_beacon_count = Column(Integer)

    device_count = Column(Integer)

    # Relations
    receiver = relationship('Receiver', foreign_keys=[receiver_id], backref='receiver_coverages')
