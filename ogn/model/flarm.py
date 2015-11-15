from sqlalchemy import Column, Integer, String, Unicode, Boolean, SmallInteger

from .base import Base


class Flarm(Base):
    __tablename__ = 'flarm'

    id = Column(Integer, primary_key=True)
    address_type = None
    address = Column(String(6), index=True)
    name = Column(Unicode)
    airport = Column(String)
    aircraft = Column(String)
    registration = Column(String(7), index=True)
    competition = Column(String(3))
    frequency = Column(String)
    tracked = Column(Boolean)
    identified = Column(Boolean)

    address_origin = Column(SmallInteger)

    def __repr__(self):
        return "<Flarm: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
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
