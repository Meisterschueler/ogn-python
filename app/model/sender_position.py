from geoalchemy2.types import Geometry
from app import db

from .aircraft_type import AircraftType


class SenderPosition(db.Model):
    __tablename__ = "sender_positions"

    reference_timestamp = db.Column(db.DateTime, primary_key=True)

    # APRS data
    name = db.Column(db.String)
    dstcall = db.Column(db.String)
    relay = db.Column(db.String)
    receiver_name = db.Column(db.String(9))
    timestamp = db.Column(db.DateTime)
    location = db.Column("location", Geometry("POINT", srid=4326))
    symboltable = None
    symbolcode = None

    track = db.Column(db.SmallInteger)
    ground_speed = db.Column(db.Float(precision=2))
    altitude = db.Column(db.Float(precision=2))

    comment = None

    # Type information
    beacon_type = None
    aprs_type = None

    # Debug information
    raw_message = None

    # Flarm specific data
    address_type = db.Column(db.SmallInteger)
    aircraft_type = db.Column(db.Enum(AircraftType), nullable=False, default=AircraftType.UNKNOWN)
    stealth = db.Column(db.Boolean)
    address = db.Column(db.String)
    climb_rate = db.Column(db.Float(precision=2))
    turn_rate = db.Column(db.Float(precision=2))
    signal_quality = db.Column(db.Float(precision=2))
    error_count = db.Column(db.SmallInteger)
    frequency_offset = db.Column(db.Float(precision=2))
    gps_quality_horizontal = db.Column(db.SmallInteger)
    gps_quality_vertical = db.Column(db.SmallInteger)
    software_version = db.Column(db.Float(precision=2))
    hardware_version = db.Column(db.SmallInteger)
    real_address = db.Column(db.String(6))
    signal_power = db.Column(db.Float(precision=2))

    #proximity = None

    # Calculated values (from parser)
    distance = db.Column(db.Float(precision=2))
    bearing = db.Column(db.SmallInteger)
    normalized_quality = db.Column(db.Float(precision=2))   # signal quality normalized to 10km

    # Calculated values (from this software)
    location_mgrs = db.Column(db.String(15))                # full mgrs (15 chars)
    location_mgrs_short = db.Column(db.String(9))           # reduced mgrs (9 chars), e.g. used for melissas range tool
    agl = db.Column(db.Float(precision=2))
