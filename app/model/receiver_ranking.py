from app import db


class ReceiverRanking(db.Model):
    __tablename__ = "receiver_rankings"

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date)
    local_rank = db.Column(db.Integer)
    global_rank = db.Column(db.Integer)

    max_distance = db.Column(db.Float(precision=2))
    max_normalized_quality = db.Column(db.Float(precision=2))
    messages_count = db.Column(db.Integer)
    coverages_count = db.Column(db.Integer)
    senders_count = db.Column(db.Integer)

    # Relations
    receiver_id = db.Column(db.Integer, db.ForeignKey("receivers.id", ondelete="CASCADE"), index=True)
    receiver = db.relationship("Receiver", foreign_keys=[receiver_id], backref=db.backref("rankings", order_by=date.desc()))

    country_id = db.Column(db.Integer, db.ForeignKey("countries.gid", ondelete="CASCADE"), index=True)
    country = db.relationship("Country", foreign_keys=[country_id], backref=db.backref("rankings", order_by=date.desc()))

    __table_args__ = (db.Index('idx_receiver_rankings_uc', 'date', 'receiver_id', unique=True), )
