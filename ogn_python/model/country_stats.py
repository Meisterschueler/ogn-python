from ogn_python import db


class CountryStats(db.Model):
    __tablename__ = "country_stats"

    id = db.Column(db.Integer, primary_key=True)

    date = db.Column(db.Date)

    # Static data
    aircraft_beacon_count = db.Column(db.Integer)
    device_count = db.Column(db.Integer)

    # Relations
    country_id = db.Column(db.Integer, db.ForeignKey('countries.gid', ondelete='SET NULL'), index=True)
    country = db.relationship('Country', foreign_keys=[country_id], backref=db.backref('stats', order_by='CountryStats.date.asc()'))

