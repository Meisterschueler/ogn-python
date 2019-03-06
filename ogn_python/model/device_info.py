from ogn_python import db


class DeviceInfo(db.Model):
    __tablename__ = 'device_infos'

    id = db.Column(db.Integer, primary_key=True)
    address_type = None
    #address = db.Column(db.String(6), index=True)
    address = db.Column(db.String, index=True)
    aircraft = db.Column(db.String)
    registration = db.Column(db.String(7))
    competition = db.Column(db.String(3))
    tracked = db.Column(db.Boolean)
    identified = db.Column(db.Boolean)
    aircraft_type = db.Column(db.SmallInteger)

    address_origin = db.Column(db.SmallInteger)

    # Relations
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id', ondelete='SET NULL'), index=True)
    device = db.relationship('Device', foreign_keys=[device_id], backref=db.backref('infos', order_by='DeviceInfo.address_origin.asc()'))

    def __repr__(self):
        return "<DeviceInfo: %s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
            self.address_type,
            self.address,
            self.aircraft,
            self.registration,
            self.competition,
            self.tracked,
            self.identified,
            self.aircraft_type,
            self.address_origin)
