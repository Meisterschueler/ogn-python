from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import null, case
from sqlalchemy.orm import backref
from app import db
from app.model import Sender


class Logbook(db.Model):
    __tablename__ = "logbook"

    id = db.Column(db.Integer, primary_key=True)

    takeoff_timestamp = db.Column(db.DateTime)
    takeoff_track = db.Column(db.SmallInteger)
    landing_timestamp = db.Column(db.DateTime)
    landing_track = db.Column(db.SmallInteger)
    max_altitude = db.Column(db.Float(precision=2))

    # Relations
    sender_id = db.Column(db.Integer, db.ForeignKey("senders.id", ondelete="CASCADE"), index=True)
    #sender = db.relationship("Sender", foreign_keys=[sender_id], backref=backref("logbook_entries", order_by=reference.desc()) # TODO: does not work...
    sender = db.relationship("Sender", foreign_keys=[sender_id], backref=backref("logbook_entries", order_by=case({True: takeoff_timestamp, False: landing_timestamp}, takeoff_timestamp != null()).desc()))

    takeoff_airport_id = db.Column(db.Integer, db.ForeignKey("airports.id", ondelete="CASCADE"), index=True)
    takeoff_airport = db.relationship("Airport", foreign_keys=[takeoff_airport_id])

    landing_airport_id = db.Column(db.Integer, db.ForeignKey("airports.id", ondelete="CASCADE"), index=True)
    landing_airport = db.relationship("Airport", foreign_keys=[landing_airport_id])

    @hybrid_property
    def duration(self):
        return None if (self.landing_timestamp is None or self.takeoff_timestamp is None) else self.landing_timestamp - self.takeoff_timestamp

    @duration.expression
    def duration(cls):
        return case({False: None, True: cls.landing_timestamp - cls.takeoff_timestamp}, cls.landing_timestamp != null() and cls.takeoff_timestamp != null())
    
    @hybrid_property
    def reference(self):
        return self.takeoff_timestamp if self.takeoff_timestamp is not None else self.landing_timestamp

    @reference.expression
    def reference(cls):
        return case({True: cls.takeoff_timestamp, False: cls.landing_timestamp}, cls.takeoff_timestamp != null())
