from geoalchemy2.shape import to_shape
from geoalchemy2.types import Geometry

from .geo import Location

from app import db

from .airport import Airport


class Receiver(db.Model):
    __tablename__ = "receivers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(9))

    location_wkt = db.Column("location", Geometry("POINT", srid=4326))
    altitude = db.Column(db.Float(precision=2))

    firstseen = db.Column(db.DateTime, index=True)
    lastseen = db.Column(db.DateTime, index=True)
    timestamp = db.Column(db.DateTime, index=True)
    version = db.Column(db.String)
    platform = db.Column(db.String)
    cpu_temp = db.Column(db.Float(precision=2))
    rec_input_noise = db.Column(db.Float(precision=2))

    agl = db.Column(db.Float(precision=2))

    # Relations
    country_id = db.Column(db.Integer, db.ForeignKey("countries.gid", ondelete="SET NULL"), index=True)
    country = db.relationship("Country", foreign_keys=[country_id], backref=db.backref("receivers", order_by="Receiver.name.asc()"))

    airport_id = db.Column(db.Integer, db.ForeignKey("airports.id", ondelete="CASCADE"), index=True)
    airport = db.relationship("Airport", foreign_keys=[airport_id], backref=db.backref("receivers", order_by="Receiver.name.asc()"))

    __table_args__ = (db.Index('idx_receivers_name_uc', 'name', unique=True), )

    @property
    def location(self):
        if self.location_wkt is None:
            return None

        coords = to_shape(self.location_wkt)
        return Location(lat=coords.y, lon=coords.x)

    def airports_nearby(self):
        query = (
            db.session.query(Airport, db.func.st_distance_sphere(self.location_wkt, Airport.location_wkt), db.func.st_azimuth(self.location_wkt, Airport.location_wkt))
            .filter(db.func.st_contains(db.func.st_buffer(Airport.location_wkt, 1), self.location_wkt))
            .filter(Airport.style.in_((2, 4, 5)))
            .order_by(db.func.st_distance_sphere(self.location_wkt, Airport.location_wkt).asc())
            .limit(5)
        )
        airports = [(airport, distance, azimuth) for airport, distance, azimuth in query]
        return airports
