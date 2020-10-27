from app import db

from sqlalchemy import Index
from sqlalchemy.orm import backref

from .aircraft_type import AircraftType

from sqlalchemy.dialects.postgresql import ENUM

class SenderPositionStatistic(db.Model):
    __tablename__ = "sender_position_statistics"

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date)

    dstcall = db.Column(db.String)
    address_type = db.Column(db.SmallInteger)
    aircraft_type = db.Column(ENUM(AircraftType, create_type=False), nullable=False, default=AircraftType.UNKNOWN)
    stealth = db.Column(db.Boolean)
    software_version = db.Column(db.Float(precision=2))
    hardware_version = db.Column(db.SmallInteger)

    messages_count = db.Column(db.Integer)

    __table_args__ = (Index('idx_sender_position_statistics_uc', 'date', 'dstcall', 'address_type', 'aircraft_type', 'stealth', 'software_version', 'hardware_version', unique=True), )
