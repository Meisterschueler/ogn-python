from sqlalchemy import Column, String, Boolean

from .beacon import Beacon


class TakeoffLanding(Beacon):
    __tablename__ = 'takeoff_landing'

    address = Column(String(6), index=True)
    is_takeoff = Column(Boolean)
