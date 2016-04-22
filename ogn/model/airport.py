from sqlalchemy import Column, String, Integer, Float, SmallInteger

from .base import Base


class Airport(Base):
    __tablename__ = "airport"

    id = Column(Integer, primary_key=True)

    name = Column(String, index=True)
    code = Column(String(5))
    country_code = Column(String(2))
    style = Column(SmallInteger)
    description = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Integer)
    runway_direction = Column(Integer)
    runway_length = Column(Integer)
    frequency = Column(Float)

    def __repr__(self):
        return "<Airport %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,% s>" % (
            self.name,
            self.code,
            self.country_code,
            self.style,
            self.description,
            self.latitude,
            self.longitude,
            self.altitude,
            self.runway_direction,
            self.runway_length,
            self.frequency)
