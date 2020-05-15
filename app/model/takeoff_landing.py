from app import db


class TakeoffLanding(db.Model):
    __tablename__ = "takeoff_landings"

    address = db.Column(db.String, primary_key=True)
    airport_id = db.Column(db.Integer, db.ForeignKey("airports.id", ondelete="SET NULL"), primary_key=True)
    timestamp = db.Column(db.DateTime, primary_key=True)

    is_takeoff = db.Column(db.Boolean)
    track = db.Column(db.SmallInteger)

    # Relations
    airport = db.relationship("Airport", foreign_keys=[airport_id], backref="takeoff_landings")
