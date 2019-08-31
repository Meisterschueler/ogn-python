from sqlalchemy.sql import func
from .beacon import Beacon

from app import db


class AircraftBeacon(Beacon):
    __tablename__ = "aircraft_beacons"

    # Flarm specific data
    address_type = db.Column(db.SmallInteger)
    aircraft_type = db.Column(db.SmallInteger)
    stealth = db.Column(db.Boolean)
    address = db.Column(db.String)
    climb_rate = db.Column(db.Float(precision=2))
    turn_rate = db.Column(db.Float(precision=2))
    signal_quality = db.Column(db.Float(precision=2))
    error_count = db.Column(db.SmallInteger)
    frequency_offset = db.Column(db.Float(precision=2))
    gps_quality_horizontal = db.Column(db.SmallInteger)
    gps_quality_vertical = db.Column(db.SmallInteger)
    software_version = db.Column(db.Float(precision=2))
    hardware_version = db.Column(db.SmallInteger)
    real_address = db.Column(db.String(6))
    signal_power = db.Column(db.Float(precision=2))
    proximity = None

    # Calculated values
    distance = db.Column(db.Float(precision=2))
    radial = db.Column(db.SmallInteger)
    quality = db.Column(db.Float(precision=2))  # signal quality normalized to 10km
    location_mgrs = db.Column(db.String(15))  # full mgrs (15 chars)
    location_mgrs_short = db.Column(db.String(9))  # reduced mgrs (9 chars), e.g. used for melissas range tool
    agl = db.Column(db.Float(precision=2))

    # Relations
    receiver_id = db.Column(db.Integer, db.ForeignKey("receivers.id", ondelete="SET NULL"))
    receiver = db.relationship("Receiver", foreign_keys=[receiver_id], backref="aircraft_beacons")

    device_id = db.Column(db.Integer, db.ForeignKey("devices.id", ondelete="SET NULL"))
    device = db.relationship("Device", foreign_keys=[device_id], backref="aircraft_beacons")

    # Multi-column indices
    db.Index("ix_aircraft_beacons_receiver_id_distance", "receiver_id", "distance")
    db.Index("ix_aircraft_beacons_device_id_timestamp", "device_id", "timestamp")

    def __repr__(self):
        return "<AircraftBeacon %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
            self.address_type,
            self.aircraft_type,
            self.stealth,
            self.address,
            self.climb_rate,
            self.turn_rate,
            self.signal_quality,
            self.error_count,
            self.frequency_offset,
            self.gps_quality_horizontal,
            self.gps_quality_vertical,
            self.software_version,
            self.hardware_version,
            self.real_address,
            self.signal_power,
            self.distance,
            self.radial,
            self.quality,
            self.location_mgrs,
            self.location_mgrs_short,
        )

    @classmethod
    def get_columns(self):
        return [
            "location",
            "altitude",
            "name",
            "dstcall",
            "relay",
            "receiver_name",
            "timestamp",
            "track",
            "ground_speed",
            #'raw_message',
            #'reference_timestamp',
            "address_type",
            "aircraft_type",
            "stealth",
            "address",
            "climb_rate",
            "turn_rate",
            "signal_quality",
            "error_count",
            "frequency_offset",
            "gps_quality_horizontal",
            "gps_quality_vertical",
            "software_version",
            "hardware_version",
            "real_address",
            "signal_power",
            "distance",
            "radial",
            "quality",
            "location_mgrs",
            "location_mgrs_short",
        ]

    def get_values(self):
        return [
            self.location_wkt,
            int(self.altitude) if self.altitude else None,
            self.name,
            self.dstcall,
            self.relay,
            self.receiver_name,
            self.timestamp,
            self.track,
            self.ground_speed,
            # self.raw_message,
            # self.reference_timestamp,
            self.address_type,
            self.aircraft_type,
            self.stealth,
            self.address,
            self.climb_rate,
            self.turn_rate,
            self.signal_quality,
            self.error_count,
            self.frequency_offset,
            self.gps_quality_horizontal,
            self.gps_quality_vertical,
            self.software_version,
            self.hardware_version,
            self.real_address,
            self.signal_power,
            self.distance,
            self.radial,
            self.quality,
            self.location_mgrs,
            self.location_mgrs_short,
        ]


db.Index("ix_aircraft_beacons_date_device_id_address", func.date(AircraftBeacon.timestamp), AircraftBeacon.device_id, AircraftBeacon.address)
db.Index("ix_aircraft_beacons_date_receiver_id_distance", func.date(AircraftBeacon.timestamp), AircraftBeacon.receiver_id, AircraftBeacon.distance)
