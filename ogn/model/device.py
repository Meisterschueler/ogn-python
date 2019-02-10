from ogn import db


class Device(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)

    #address = db.Column(db.String(6), index=True)
    address = db.Column(db.String, index=True)
    firstseen = db.Column(db.DateTime, index=True)
    lastseen = db.Column(db.DateTime, index=True)
    aircraft_type = db.Column(db.SmallInteger, index=True)
    stealth = db.Column(db.Boolean)
    software_version = db.Column(db.Float(precision=2))
    hardware_version = db.Column(db.SmallInteger)
    real_address = db.Column(db.String(6))

    def __repr__(self):
        return "<Device: %s,%s,%s,%s,%s,%s>" % (
            self.address,
            self.aircraft_type,
            self.stealth,
            self.software_version,
            self.hardware_version,
            self.real_address)
