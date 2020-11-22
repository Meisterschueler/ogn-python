from sqlalchemy.ext.hybrid import hybrid_property

from app import db


class Logbook(db.Model):
    __tablename__ = "logbooks"

    id = db.Column(db.Integer, primary_key=True)

    takeoff_timestamp = db.Column(db.DateTime)
    takeoff_track = db.Column(db.SmallInteger)
    landing_timestamp = db.Column(db.DateTime)
    landing_track = db.Column(db.SmallInteger)
    max_altitude = db.Column(db.Float(precision=2))

    # Relations
    sender_id = db.Column(db.Integer, db.ForeignKey("senders.id", ondelete="CASCADE"), index=True)
    sender = db.relationship("Sender", foreign_keys=[sender_id], backref=db.backref("logbook_entries", order_by=db.case({True: takeoff_timestamp, False: landing_timestamp}, takeoff_timestamp != db.null()).desc()))

    takeoff_airport_id = db.Column(db.Integer, db.ForeignKey("airports.id", ondelete="CASCADE"), index=True)
    takeoff_airport = db.relationship("Airport", foreign_keys=[takeoff_airport_id], backref=db.backref("logbook_entries_takeoff", order_by=db.case({True: takeoff_timestamp, False: landing_timestamp}, takeoff_timestamp != db.null()).desc()))

    takeoff_country_id = db.Column(db.Integer, db.ForeignKey("countries.gid", ondelete="CASCADE"), index=True)
    takeoff_country = db.relationship("Country", foreign_keys=[takeoff_country_id], backref=db.backref("logbook_entries_takeoff", order_by=db.case({True: takeoff_timestamp, False: landing_timestamp}, takeoff_timestamp != db.null()).desc()))

    landing_airport_id = db.Column(db.Integer, db.ForeignKey("airports.id", ondelete="CASCADE"), index=True)
    landing_airport = db.relationship("Airport", foreign_keys=[landing_airport_id], backref=db.backref("logbook_entries_landing", order_by=db.case({True: takeoff_timestamp, False: landing_timestamp}, takeoff_timestamp != db.null()).desc()))

    landing_country_id = db.Column(db.Integer, db.ForeignKey("countries.gid", ondelete="CASCADE"), index=True)
    landing_country = db.relationship("Country", foreign_keys=[landing_country_id], backref=db.backref("logbook_entries_landing", order_by=db.case({True: takeoff_timestamp, False: landing_timestamp}, takeoff_timestamp != db.null()).desc()))

    @hybrid_property
    def duration(self):
        return None if (self.landing_timestamp is None or self.takeoff_timestamp is None) else self.landing_timestamp - self.takeoff_timestamp

    @duration.expression
    def duration(cls):
        return db.case({False: None, True: cls.landing_timestamp - cls.takeoff_timestamp}, cls.landing_timestamp != db.null() and cls.takeoff_timestamp != db.null())

    @hybrid_property
    def reference_timestamp(self):
        return self.takeoff_timestamp if self.takeoff_timestamp is not None else self.landing_timestamp

    @reference_timestamp.expression
    def reference_timestamp(cls):
        return db.case({True: cls.takeoff_timestamp, False: cls.landing_timestamp}, cls.takeoff_timestamp != db.null())

    #__table_args__ = (db.Index('idx_logbook_reference_timestamp', db.case({True: takeoff_timestamp, False: landing_timestamp}, takeoff_timestamp != db.null())),)
    # FIXME: does not work...

# FIXME: this does not throw an error as the __table_args__ above, but there is no index created
#_wrapped_case = f"({db.case(whens={True: Logbook.takeoff_timestamp, False: Logbook.landing_timestamp}, value=Logbook.takeoff_timestamp != db.null())})"
#Index("idx_logbook_reference_timestamp", _wrapped_case)

# TODO:
# so execute manually: CREATE INDEX IF NOT EXISTS idx_logbook_reference_timestamp ON logbooks ((CASE takeoff_timestamp IS NULL WHEN true THEN takeoff_timestamp WHEN false THEN landing_timestamp END));
