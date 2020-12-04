from app import db


class ReceiverStatusStatistic(db.Model):
    __tablename__ = "receiver_status_statistics"

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date, nullable=False)

    version = db.Column(db.String, nullable=False)
    platform = db.Column(db.String, nullable=False)

    messages_count = db.Column(db.Integer)

    # Relations
    receiver_id = db.Column(db.Integer, db.ForeignKey("receivers.id", ondelete="CASCADE"), index=True)
    receiver = db.relationship("Receiver", foreign_keys=[receiver_id], backref=db.backref("status_statistics", order_by=date.desc()))

    __table_args__ = (db.Index('idx_receiver_status_statistics_uc', 'date', 'receiver_id', 'version', 'platform', unique=True), )
