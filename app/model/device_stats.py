from app import db

from .aircraft_type import AircraftType


class DeviceStats(db.Model):
    __tablename__ = "device_stats"

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date)

    # Static data
    name = db.Column(db.String)
    firstseen = db.Column(db.DateTime)
    lastseen = db.Column(db.DateTime)
    aircraft_type = db.Column(db.Enum(AircraftType), nullable=False, default=AircraftType.UNKNOWN)
    stealth = db.Column(db.Boolean)
    software_version = db.Column(db.Float(precision=2))
    hardware_version = db.Column(db.SmallInteger)
    real_address = db.Column(db.String(6))

    # Statistic data
    max_altitude = db.Column(db.Float(precision=2))
    receiver_count = db.Column(db.SmallInteger)
    aircraft_beacon_count = db.Column(db.Integer)
    jumps = db.Column(db.SmallInteger)
    ambiguous = db.Column(db.Boolean)
    quality = db.Column(db.Float(precision=2))

    # Relation statistic data
    quality_offset = db.Column(db.Float(precision=2))

    # Ranking data
    max_altitude_ranking_worldwide = db.Column(db.Integer)
    max_altitude_ranking_country = db.Column(db.Integer)
    receiver_count_ranking_worldwide = db.Column(db.Integer)
    receiver_count_ranking_country = db.Column(db.Integer)
    aircraft_beacon_count_ranking_worldwide = db.Column(db.Integer)
    aircraft_beacon_count_ranking_country = db.Column(db.Integer)
    quality_ranking_worldwide = db.Column(db.Integer)
    quality_ranking_country = db.Column(db.Integer)

    # Relations
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id", ondelete="SET NULL"), index=True)
    device = db.relationship("Device", foreign_keys=[device_id], backref=db.backref("stats", order_by="DeviceStats.date.asc()"))

    def __repr__(self):
        return "<DeviceStats: %s,%s,%s,%s>" % (self.date, self.receiver_count, self.aircraft_beacon_count, self.max_altitude)


db.Index("ix_device_stats_date_device_id", DeviceStats.date, DeviceStats.device_id)
