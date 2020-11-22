from app import db


class ReceiverStatistic(db.Model):
    __tablename__ = "receiver_statistics"

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date)
    is_trustworthy = db.Column(db.Boolean)

    max_distance = db.Column(db.Float(precision=2))
    max_normalized_quality = db.Column(db.Float(precision=2))
    messages_count = db.Column(db.Integer)
    coverages_count = db.Column(db.Integer)
    senders_count = db.Column(db.Integer)

    # Relations
    receiver_id = db.Column(db.Integer, db.ForeignKey("receivers.id", ondelete="CASCADE"), index=True)
    receiver = db.relationship("Receiver", foreign_keys=[receiver_id], backref=db.backref("statistics", order_by=date.desc()))

    __table_args__ = (db.Index('idx_receiver_statistics_uc', 'date', 'receiver_id', 'is_trustworthy', unique=True), )
