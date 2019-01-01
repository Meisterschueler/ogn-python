from sqlalchemy import Column, String, Integer, SmallInteger, Float, Date, ForeignKey
from sqlalchemy.orm import relationship, backref


from .base import Base


class ReceiverCoverage(Base):
    __tablename__ = "receiver_coverages"

    location_mgrs = Column(String(9), primary_key=True)
    receiver_id = Column(Integer, ForeignKey('receivers.id', ondelete='SET NULL'), primary_key=True)
    date = Column(Date, primary_key=True)

    max_signal_quality = Column(Float)
    max_altitude = Column(Float(precision=2))
    min_altitude = Column(Float(precision=2))
    aircraft_beacon_count = Column(Integer)

    device_count = Column(SmallInteger)

    # Relations
    receiver_id = Column(Integer, ForeignKey('receivers.id', ondelete='SET NULL'), index=True)
    receiver = relationship('Receiver', foreign_keys=[receiver_id], backref=backref('receiver_coverages', order_by='ReceiverCoverage.date.asc()'))
