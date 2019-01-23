from sqlalchemy import Column, String, Integer, SmallInteger, Float, Date, ForeignKey, Index
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func


from .base import Base


class ReceiverCoverage(Base):
    __tablename__ = "receiver_coverages"

    location_mgrs_short = Column(String(9), primary_key=True)
    date = Column(Date, primary_key=True)

    max_signal_quality = Column(Float)
    max_altitude = Column(Float(precision=2))
    min_altitude = Column(Float(precision=2))
    aircraft_beacon_count = Column(Integer)

    device_count = Column(SmallInteger)

    # Relations
    receiver_id = Column(Integer, ForeignKey('receivers.id', ondelete='SET NULL'), primary_key=True)
    receiver = relationship('Receiver', foreign_keys=[receiver_id], backref=backref('receiver_coverages', order_by='ReceiverCoverage.date.asc()'))


Index('ix_receiver_coverages_date_receiver_id', ReceiverCoverage.date, ReceiverCoverage.receiver_id)
Index('ix_receiver_coverages_receiver_id_date', ReceiverCoverage.receiver_id, ReceiverCoverage.date)
