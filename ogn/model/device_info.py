from sqlalchemy import Column, Integer, String, Boolean, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship, backref

from .base import Base


class DeviceInfo(Base):
    __tablename__ = 'device_infos'

    id = Column(Integer, primary_key=True)
    address_type = None
    #address = Column(String(6), index=True)
    address = Column(String, index=True)
    aircraft = Column(String)
    registration = Column(String(7))
    competition = Column(String(3))
    tracked = Column(Boolean)
    identified = Column(Boolean)
    aircraft_type = Column(SmallInteger)

    address_origin = Column(SmallInteger)

    # Relations
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='SET NULL'), index=True)
    device = relationship('Device', foreign_keys=[device_id], backref=backref('infos', order_by='DeviceInfo.address_origin.asc()'))

    def __repr__(self):
        return "<DeviceInfo: %s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
            self.address_type,
            self.address,
            self.aircraft,
            self.registration,
            self.competition,
            self.tracked,
            self.identified,
            self.aircraft_type,
            self.address_origin)
