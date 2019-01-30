from geoalchemy2.types import Geometry
from sqlalchemy import Column, Integer, Date, Index, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Flight2D(Base):
    __tablename__ = "flights2d"

    date = Column(Date, primary_key=True)

    path_wkt = Column('path', Geometry('MULTILINESTRING', srid=4326))
    path_simple_wkt = Column('path_simple', Geometry('MULTILINESTRING', srid=4326))     # this is the path simplified with ST_Simplify(path, 0.0001)

    # Relations
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='SET NULL'), primary_key=True)
    device = relationship('Device', foreign_keys=[device_id], backref='flights2d')

    def __repr__(self):
        return "<Flight %s: %s,%s>" % (
            self.date,
            self.path_wkt,
            self.path_simple_wkt)


Index('ix_flights2d_date_device_id', Flight2D.date, Flight2D.device_id)
#Index('ix_flights2d_date_path', Flight2D.date, Flight2D.path_wkt) --> CREATE INDEX ix_flights2d_date_path ON flights2d USING GIST("date", path)
