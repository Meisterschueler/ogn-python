from app import db


class RelationStatistic(db.Model):
    __tablename__ = "relation_statistics"

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date)
    is_trustworthy = db.Column(db.Boolean)

    max_distance = db.Column(db.Float(precision=2))
    max_normalized_quality = db.Column(db.Float(precision=2))
    messages_count = db.Column(db.Integer)

    # Relations
    sender_id = db.Column(db.Integer, db.ForeignKey("senders.id", ondelete="CASCADE"), index=True)
    sender = db.relationship("Sender", foreign_keys=[sender_id], backref=db.backref("relation_stats", order_by=date))

    receiver_id = db.Column(db.Integer, db.ForeignKey("receivers.id", ondelete="CASCADE"), index=True)
    receiver = db.relationship("Receiver", foreign_keys=[receiver_id], backref=db.backref("relation_stats", order_by=date))

    __table_args__ = (db.Index('idx_relation_statistics_uc', 'date', 'sender_id', 'receiver_id', 'is_trustworthy', unique=True), )
