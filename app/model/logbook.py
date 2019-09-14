from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import null, case
from app import db


class Logbook(db.Model):
    __tablename__ = "logbook"

    id = db.Column(db.Integer, primary_key=True)

    reftime = db.Column(db.DateTime, index=True)
    takeoff_timestamp = db.Column(db.DateTime)
    takeoff_track = db.Column(db.SmallInteger)
    landing_timestamp = db.Column(db.DateTime)
    landing_track = db.Column(db.SmallInteger)
    max_altitude = db.Column(db.Float(precision=2))

    # Relations
    takeoff_airport_id = db.Column(db.Integer, db.ForeignKey("airports.id", ondelete="CASCADE"), index=True)
    takeoff_airport = db.relationship("Airport", foreign_keys=[takeoff_airport_id])

    landing_airport_id = db.Column(db.Integer, db.ForeignKey("airports.id", ondelete="CASCADE"), index=True)
    landing_airport = db.relationship("Airport", foreign_keys=[landing_airport_id])

    device_id = db.Column(db.Integer, db.ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    device = db.relationship("Device", foreign_keys=[device_id], backref=db.backref("logbook", order_by="Logbook.reftime"))

    @hybrid_property
    def duration(self):
        return None if (self.landing_timestamp is None or self.takeoff_timestamp is None) else self.landing_timestamp - self.takeoff_timestamp

    @duration.expression
    def duration(cls):
        return case({False: None, True: cls.landing_timestamp - cls.takeoff_timestamp}, cls.landing_timestamp != null() and cls.takeoff_timestamp != null())
