from sqlalchemy import Column, Integer, String, Boolean, SmallInteger

from .base import Base


class DeviceInfo(Base):
    __tablename__ = 'device_info'

    id = Column(Integer, primary_key=True)
    address_type = None
    address = Column(String(6), index=True)
    aircraft = Column(String)
    registration = Column(String(7))
    competition = Column(String(3))
    tracked = Column(Boolean)
    identified = Column(Boolean)
    aircraft_type = Column(SmallInteger)

    address_origin = Column(SmallInteger)

    def __repr__(self):
        return "<DeviceInfo: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
            self.address_type,
            self.address,
            self.name,
            self.airport,
            self.aircraft,
            self.registration,
            self.competition,
            self.frequency,
            self.tracked,
            self.identified)
