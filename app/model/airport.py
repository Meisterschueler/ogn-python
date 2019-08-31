from geoalchemy2.types import Geometry

from app import db


class Airport(db.Model):
    __tablename__ = "airports"

    id = db.Column(db.Integer, primary_key=True)

    location_wkt = db.Column("location", Geometry("POINT", srid=4326))
    altitude = db.Column(db.Float(precision=2))

    name = db.Column(db.String, index=True)
    code = db.Column(db.String(6))
    country_code = db.Column(db.String(2))
    style = db.Column(db.SmallInteger)
    description = db.Column(db.String)
    runway_direction = db.Column(db.SmallInteger)
    runway_length = db.Column(db.SmallInteger)
    frequency = db.Column(db.Float(precision=2))

    border = db.Column("border", Geometry("POLYGON", srid=4326))

    def __repr__(self):
        return "<Airport %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,% s>" % (
            self.name,
            self.code,
            self.country_code,
            self.style,
            self.description,
            self.location_wkt.latitude,
            self.location_wkt.longitude,
            self.altitude,
            self.runway_direction,
            self.runway_length,
            self.frequency,
        )
