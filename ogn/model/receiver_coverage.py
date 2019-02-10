from ogn import db


class ReceiverCoverage(db.Model):
    __tablename__ = "receiver_coverages"

    location_mgrs_short = db.Column(db.String(9), primary_key=True)
    date = db.Column(db.Date, primary_key=True)

    max_signal_quality = db.Column(db.Float)
    max_altitude = db.Column(db.Float(precision=2))
    min_altitude = db.Column(db.Float(precision=2))
    aircraft_beacon_count = db.Column(db.Integer)

    device_count = db.Column(db.SmallInteger)

    # Relations
    receiver_id = db.Column(db.Integer, db.ForeignKey('receivers.id', ondelete='SET NULL'), primary_key=True)
    receiver = db.relationship('Receiver', foreign_keys=[receiver_id], backref=db.backref('receiver_coverages', order_by='ReceiverCoverage.date.asc()'))


db.Index('ix_receiver_coverages_date_receiver_id', ReceiverCoverage.date, ReceiverCoverage.receiver_id)
db.Index('ix_receiver_coverages_receiver_id_date', ReceiverCoverage.receiver_id, ReceiverCoverage.date)
