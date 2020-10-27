from geoalchemy2.types import Geometry
from app import db


class ReceiverPosition(db.Model):
    __tablename__ = "receiver_positions"

    reference_timestamp = db.Column(db.DateTime, primary_key=True)

    # APRS data
    name = db.Column(db.String)
    dstcall = db.Column(db.String)
    #relay = db.Column(db.String)
    receiver_name = db.Column(db.String(9))
    timestamp = db.Column(db.DateTime)
    location = db.Column("location", Geometry("POINT", srid=4326))
    symboltable = None
    symbolcode = None

    #track = db.Column(db.SmallInteger)
    #ground_speed = db.Column(db.Float(precision=2))
    altitude = db.Column(db.Float(precision=2))

    comment = None

    # Type information
    beacon_type = None
    aprs_type = None

    # Debug information
    raw_message = None

    # Receiver specific data
    user_comment = None

    # Calculated values (from this software)
    location_mgrs = db.Column(db.String(15))                # full mgrs (15 chars)
    location_mgrs_short = db.Column(db.String(9))           # reduced mgrs (9 chars), e.g. used for melissas range tool
    agl = db.Column(db.Float(precision=2))
