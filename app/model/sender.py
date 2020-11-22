import datetime

from sqlalchemy.ext.hybrid import hybrid_property

from app import db
from app.model.aircraft_type import AircraftType


class Sender(db.Model):
    __tablename__ = "senders"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    address = db.Column(db.String(6), index=True)
    firstseen = db.Column(db.DateTime, index=True)
    lastseen = db.Column(db.DateTime, index=True)
    aircraft_type = db.Column(db.Enum(AircraftType), nullable=False, default=AircraftType.UNKNOWN)
    stealth = db.Column(db.Boolean)
    software_version = db.Column(db.Float(precision=2))
    hardware_version = db.Column(db.SmallInteger)
    real_address = db.Column(db.String(6))

    __table_args__ = (db.Index('idx_senders_name_uc', 'name', unique=True), )

    def __repr__(self):
        return "<Sender: %s,%s,%s,%s,%s,%s>" % (self.address, self.aircraft_type, self.stealth, self.software_version, self.hardware_version, self.real_address)

    EXPIRY_DATES = {
        7.01: datetime.date(2022, 2, 28),
        7.0: datetime.date(2021, 10, 31),
        6.83: datetime.date(2021, 10, 31),
        6.82: datetime.date(2021, 5, 31),
        6.81: datetime.date(2021, 1, 31),
        6.80: datetime.date(2021, 1, 31),
        6.67: datetime.date(2020, 10, 31),
        6.63: datetime.date(2020, 5, 31),
        6.62: datetime.date(2020, 5, 31),
        6.6: datetime.date(2020, 1, 31),
        6.42: datetime.date(2019, 10, 31),
        6.41: datetime.date(2019, 1, 31),
        6.4: datetime.date(2019, 1, 31),
        6.09: datetime.date(2018, 9, 30),
        6.08: datetime.date(2018, 9, 30),
        6.07: datetime.date(2018, 3, 31),
        6.06: datetime.date(2017, 9, 30),
        6.05: datetime.date(2017, 3, 31),
    }

    def expiry_date(self):
        if self.name.startswith("FLR"):
            if self.software_version in self.EXPIRY_DATES:
                return self.EXPIRY_DATES[self.software_version]
            else:
                return datetime.date(2000, 1, 1)
        else:
            return None
