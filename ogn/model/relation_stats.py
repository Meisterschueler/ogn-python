from sqlalchemy import Column, Integer, Date, Float, ForeignKey, Index
from sqlalchemy.orm import relationship

from ogn import db


class RelationStats(db.Model):
    __tablename__ = "relation_stats"

    id = Column(Integer, primary_key=True)

    date = Column(Date)

    # Statistic data
    quality = Column(Float(precision=2))
    beacon_count = Column(Integer)

    # Relations
    device_id = Column(Integer, ForeignKey('devices.id', ondelete='SET NULL'), index=True)
    device = relationship('Device', foreign_keys=[device_id], backref='relation_stats')
    receiver_id = Column(Integer, ForeignKey('receivers.id', ondelete='SET NULL'), index=True)
    receiver = relationship('Receiver', foreign_keys=[receiver_id], backref='relation_stats')

    def __repr__(self):
        return "<RelationStats: %s,%s,%s>" % (
            self.date,
            self.quality,
            self.beacon_count)


Index('ix_relation_stats_date_device_id', RelationStats.date, RelationStats.device_id, RelationStats.receiver_id)
Index('ix_relation_stats_date_receiver_id', RelationStats.date, RelationStats.receiver_id, RelationStats.device_id)
