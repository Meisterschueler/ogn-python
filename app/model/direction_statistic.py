from app import db

from sqlalchemy.dialects.postgresql import JSON


class DirectionStatistic(db.Model):
    __tablename__ = "direction_statistics"

    id = db.Column(db.Integer, primary_key=True)

    directions_count = db.Column(db.Integer)
    messages_count = db.Column(db.Integer)
    direction_data = db.Column(db.JSON)

    # Relations
    sender_id = db.Column(db.Integer, db.ForeignKey("senders.id", ondelete="CASCADE"), index=True)
    sender = db.relationship("Sender", foreign_keys=[sender_id], backref=db.backref("direction_stats", order_by=directions_count.desc()))

    receiver_id = db.Column(db.Integer, db.ForeignKey("receivers.id", ondelete="CASCADE"), index=True)
    receiver = db.relationship("Receiver", foreign_keys=[receiver_id], backref=db.backref("direction_stats", order_by=directions_count.desc()))

    __table_args__ = (db.Index('idx_direction_statistics_uc', 'sender_id', 'receiver_id', unique=True), )
