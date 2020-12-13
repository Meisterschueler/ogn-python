from app import db


class CoverageStatistic(db.Model):
    __tablename__ = "coverage_statistics"

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date)
    location_mgrs_short = db.Column(db.String(9))
    is_trustworthy = db.Column(db.Boolean)

    messages_count = db.Column(db.Integer)
    max_distance = db.Column(db.Float(precision=2))
    max_normalized_quality = db.Column(db.Float(precision=2))
    max_signal_quality = db.Column(db.Float(precision=2))
    min_altitude = db.Column(db.Float(precision=2))
    max_altitude = db.Column(db.Float(precision=2))

    # Relations
    sender_id = db.Column(db.Integer, db.ForeignKey("senders.id", ondelete="CASCADE"), index=True)
    sender = db.relationship("Sender", foreign_keys=[sender_id], backref=db.backref("coverage_stats", order_by=date))

    receiver_id = db.Column(db.Integer, db.ForeignKey("receivers.id", ondelete="CASCADE"), index=True)
    receiver = db.relationship("Receiver", foreign_keys=[receiver_id], backref=db.backref("coverage_stats", order_by=date))

    __table_args__ = (db.Index('idx_coverage_statistics_uc', 'date', 'location_mgrs_short', 'sender_id', 'receiver_id', 'is_trustworthy', unique=True), )
