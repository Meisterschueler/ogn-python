from sqlalchemy import Column, String, Integer, Float, Boolean, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship

from .beacon import Beacon


class AircraftBeacon(Beacon):
    __tablename__ = "aircraft_beacon"

    # Flarm specific data
    address_type = Column(SmallInteger)
    aircraft_type = Column(SmallInteger, index=True)
    stealth = Column(Boolean)
    address = Column(String(6))
    climb_rate = Column(Float)
    turn_rate = Column(Float)
    signal_strength = Column(Float)
    error_count = Column(Integer)
    frequency_offset = Column(Float)
    gps_status = Column(String)

    software_version = Column(Float)
    hardware_version = Column(SmallInteger)
    real_address = Column(String(6))

    flightlevel = Column(Float)

    # Relations
    receiver_id = Column(Integer, ForeignKey('receiver.id', ondelete='SET NULL'), index=True)
    receiver = relationship('Receiver', foreign_keys=[receiver_id])

    device_id = Column(Integer, ForeignKey('device.id', ondelete='SET NULL'), index=True)
    device = relationship('Device', foreign_keys=[device_id])

    def __repr__(self):
        return "<AircraftBeacon %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
            self.name,
            self.address_type,
            self.aircraft_type,
            self.timestamp,
            self.address_type,
            self.aircraft_type,
            self.stealth,
            self.address,
            self.climb_rate,
            self.turn_rate,
            self.signal_strength,
            self.error_count,
            self.frequency_offset,
            self.gps_status)
