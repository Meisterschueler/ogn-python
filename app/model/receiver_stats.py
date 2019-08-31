from geoalchemy2.types import Geometry

from app import db


class ReceiverStats(db.Model):
    __tablename__ = "receiver_stats"

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date)

    # Static data
    firstseen = db.Column(db.DateTime, index=True)
    lastseen = db.Column(db.DateTime, index=True)
    location_wkt = db.Column("location", Geometry("POINT", srid=4326))
    altitude = db.Column(db.Float(precision=2))
    version = db.Column(db.String)
    platform = db.Column(db.String)

    # Statistic data
    aircraft_beacon_count = db.Column(db.Integer)
    aircraft_count = db.Column(db.SmallInteger)
    max_distance = db.Column(db.Float)
    quality = db.Column(db.Float(precision=2))

    # Relation statistic data
    quality_offset = db.Column(db.Float(precision=2))

    # Ranking data
    aircraft_beacon_count_ranking = db.Column(db.SmallInteger)
    aircraft_count_ranking = db.Column(db.SmallInteger)
    max_distance_ranking = db.Column(db.SmallInteger)
    quality_ranking = db.Column(db.Integer)

    # Relations
    receiver_id = db.Column(db.Integer, db.ForeignKey("receivers.id", ondelete="SET NULL"), index=True)
    receiver = db.relationship("Receiver", foreign_keys=[receiver_id], backref=db.backref("stats", order_by="ReceiverStats.date.asc()"))


db.Index("ix_receiver_stats_date_receiver_id", ReceiverStats.date, ReceiverStats.receiver_id)
