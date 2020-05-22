from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.ext.hybrid import hybrid_property

from .geo import Location

from app import db


class Beacon(AbstractConcreteBase, db.Model):
    # APRS data
    location = db.Column("location", Geometry("POINT", srid=4326))
    altitude = db.Column(db.Float(precision=2))

    name = db.Column(db.String, primary_key=True)
    dstcall = db.Column(db.String)
    relay = db.Column(db.String)
    receiver_name = db.Column(db.String(9), primary_key=True)
    timestamp = db.Column(db.DateTime, primary_key=True)
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
    reference_timestamp = db.Column(db.DateTime, nullable=False)
