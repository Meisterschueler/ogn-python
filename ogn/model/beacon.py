from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.ext.declarative import AbstractConcreteBase

from .base import Base


class Beacon(AbstractConcreteBase, Base):
    id = Column(Integer, primary_key=True)

    # APRS data
    name = Column(String)
    receiver_name = Column(String(9))
    timestamp = Column(DateTime, index=True)
    latitude = Column(Float)
    symboltable = None
    longitude = Column(Float)
    symbolcode = None
    track = Column(Integer)
    ground_speed = Column(Float)
    altitude = Column(Integer)
    comment = None
