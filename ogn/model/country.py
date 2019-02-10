from geoalchemy2.types import Geometry

from ogn import db


class Country(db.Model):
    __tablename__ = "countries"

    gid = db.Column(db.Integer, primary_key=True)

    fips = db.Column(db.String(2))
    iso2 = db.Column(db.String(2))
    iso3 = db.Column(db.String(3))

    un = db.Column(db.SmallInteger)
    name = db.Column(db.String(50))
    area = db.Column(db.Integer)
    pop2005 = db.Column(db.BigInteger)
    region = db.Column(db.SmallInteger)
    subregion = db.Column(db.SmallInteger)
    lon = db.Column(db.Float)
    lat = db.Column(db.Float)

    geom = db.Column('geom', Geometry('MULTIPOLYGON', srid=4326))

    def __repr__(self):
        return "<Country %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
            self.fips,
            self.iso2,
            self.iso3,
            self.un,
            self.name,
            self.area,
            self.pop2005,
            self.region,
            self.subregion,
            self.lon,
            self.lat)
