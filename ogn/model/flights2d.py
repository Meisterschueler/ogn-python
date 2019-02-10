from geoalchemy2.types import Geometry

from ogn import db


class Flight2D(db.Model):
    __tablename__ = "flights2d"

    date = db.Column(db.Date, primary_key=True)

    path_wkt = db.Column('path', Geometry('MULTILINESTRING', srid=4326))
    path_simple_wkt = db.Column('path_simple', Geometry('MULTILINESTRING', srid=4326))     # this is the path simplified with ST_Simplify(path, 0.0001)

    # Relations
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id', ondelete='SET NULL'), primary_key=True)
    device = db.relationship('Device', foreign_keys=[device_id], backref='flights2d')

    def __repr__(self):
        return "<Flight %s: %s,%s>" % (
            self.date,
            self.path_wkt,
            self.path_simple_wkt)


db.Index('ix_flights2d_date_device_id', Flight2D.date, Flight2D.device_id)
#db.Index('ix_flights2d_date_path', Flight2D.date, Flight2D.path_wkt) --> CREATE INDEX ix_flights2d_date_path ON flights2d USING GIST("date", path)
