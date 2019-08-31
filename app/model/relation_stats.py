from app import db


class RelationStats(db.Model):
    __tablename__ = "relation_stats"

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date)

    # Statistic data
    quality = db.Column(db.Float(precision=2))
    beacon_count = db.Column(db.Integer)

    # Relations
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id", ondelete="SET NULL"), index=True)
    device = db.relationship("Device", foreign_keys=[device_id], backref="relation_stats")
    receiver_id = db.Column(db.Integer, db.ForeignKey("receivers.id", ondelete="SET NULL"), index=True)
    receiver = db.relationship("Receiver", foreign_keys=[receiver_id], backref="relation_stats")

    def __repr__(self):
        return "<RelationStats: %s,%s,%s>" % (self.date, self.quality, self.beacon_count)


db.Index("ix_relation_stats_date_device_id", RelationStats.date, RelationStats.device_id, RelationStats.receiver_id)
db.Index("ix_relation_stats_date_receiver_id", RelationStats.date, RelationStats.receiver_id, RelationStats.device_id)
