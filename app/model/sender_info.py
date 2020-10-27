from app import db
from .sender_info_origin import SenderInfoOrigin
from .aircraft_type import AircraftType

from sqlalchemy.orm import backref
#from sqlalchemy.dialects.postgresql import ENUM

class SenderInfo(db.Model):
    __tablename__ = "sender_infos"

    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(6), index=True)
    address_type = None
    aircraft = db.Column(db.String)
    registration = db.Column(db.String(7))
    competition = db.Column(db.String(3))
    tracked = db.Column(db.Boolean)
    identified = db.Column(db.Boolean)
    aircraft_type = db.Column(db.Enum(AircraftType), nullable=False, default=AircraftType.UNKNOWN)

    address_origin = db.Column(db.Enum(SenderInfoOrigin), nullable=False, default=SenderInfoOrigin.UNKNOWN)

    # Relations
    sender_id = db.Column(db.Integer, db.ForeignKey("senders.id"), index=True)
    sender = db.relationship("Sender", foreign_keys=[sender_id], backref=backref("infos", order_by=address_origin))

    def __repr__(self):
        return "<SenderInfo: %s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
            self.address_type,
            self.address,
            self.aircraft,
            self.registration,
            self.competition,
            self.tracked,
            self.identified,
            self.aircraft_type,
            self.address_origin,
        )
