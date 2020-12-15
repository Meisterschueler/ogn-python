from app import db


class AggregateCoverageStatistic(db.Model):
    __tablename__ = "aggregate_coverage_statistics"

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
    senders_count = db.Column(db.Integer)
    receivers_count = db.Column(db.Integer)

    __table_args__ = (db.Index('idx_aggregate_coverage_statistics_uc', 'date', 'location_mgrs_short', 'is_trustworthy', unique=True), )
