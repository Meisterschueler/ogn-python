from sqlalchemy import Column, Integer, String, Float, Boolean, SmallInteger, DateTime
from sqlalchemy.orm import relationship

from .base import Base


class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)

    #address = Column(String(6), index=True)
    address = Column(String, index=True)
    firstseen = Column(DateTime, index=True)
    lastseen = Column(DateTime, index=True)
    aircraft_type = Column(SmallInteger, index=True)
    stealth = Column(Boolean)
    software_version = Column(Float(precision=2))
    hardware_version = Column(SmallInteger)
    real_address = Column(String(6))

    def __repr__(self):
        return "<Device: %s,%s,%s,%s,%s,%s>" % (
            self.address,
            self.aircraft_type,
            self.stealth,
            self.software_version,
            self.hardware_version,
            self.real_address)
