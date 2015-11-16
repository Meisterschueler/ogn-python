from sqlalchemy import Column, String, Integer, Float, DateTime

from .base import Base


class Receiver(Base):
    __tablename__ = "receiver"

    id = Column(Integer, primary_key=True)
    name = Column(String(9))
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Integer)
    firstseen = Column(DateTime, index=True)
    lastseen = Column(DateTime, index=True)
    country_code = Column(String(2))
    version = Column(String)
    platform = Column(String)
