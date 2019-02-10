from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry

from .geo import Location

from ogn import db


class Receiver(db.Model):
    __tablename__ = "receivers"

    id = db.Column(db.Integer, primary_key=True)

    location_wkt = db.Column('location', Geometry('POINT', srid=4326))
    altitude = db.Column(db.Float(precision=2))

    name = db.Column(db.String(9), index=True)
    firstseen = db.Column(db.DateTime, index=True)
    lastseen = db.Column(db.DateTime, index=True)
    version = db.Column(db.String)
    platform = db.Column(db.String)

    # Relations
    country_id = db.Column(db.Integer, db.ForeignKey('countries.gid', ondelete='SET NULL'), index=True)
    country = db.relationship('Country', foreign_keys=[country_id], backref=db.backref('receivers', order_by='Receiver.name.asc()'))

    @property
    def location(self):
        if self.location_wkt is None:
            return None

        coords = to_shape(self.location_wkt)
        return Location(lat=coords.y, lon=coords.x)
