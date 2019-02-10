from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.ext.hybrid import hybrid_property

from .geo import Location

from ogn import db


class Beacon(AbstractConcreteBase, db.Model):
    # APRS data
    location_wkt = db.Column('location', Geometry('POINT', srid=4326))
    altitude = db.Column(db.Float(precision=2))

    name = db.Column(db.String, primary_key=True, nullable=True)
    dstcall = db.Column(db.String)
    relay = db.Column(db.String)
    receiver_name = db.Column(db.String(9), primary_key=True, nullable=True)
    timestamp = db.Column(db.DateTime, primary_key=True, nullable=True)
    symboltable = None
    symbolcode = None
    track = db.Column(db.SmallInteger)
    ground_speed = db.Column(db.Float(precision=2))
    comment = None

    # Type information
    beacon_type = None
    aprs_type = None

    # Debug information
    raw_message = None
    reference_timestamp = None

    @hybrid_property
    def location(self):
        if self.location_wkt is None:
            return None

        coords = to_shape(self.location_wkt)
        return Location(lat=coords.y, lon=coords.x)

    @location.expression
    def location(cls):
        return cls.location_wkt
