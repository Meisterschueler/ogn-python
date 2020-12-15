from app import db


class SenderCoverageStatistic(db.Model):
    __tablename__ = "sender_coverage_statistics"

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
    receivers_count = db.Column(db.Integer)

    # Relations
    sender_id = db.Column(db.Integer, db.ForeignKey("senders.id", ondelete="CASCADE"), index=True)
    sender = db.relationship("Sender", foreign_keys=[sender_id], backref=db.backref("sender_coverage_stats", order_by=date))

    __table_args__ = (db.Index('idx_sender_coverage_statistics_uc', 'date', 'sender_id', 'location_mgrs_short', 'is_trustworthy', unique=True), )
