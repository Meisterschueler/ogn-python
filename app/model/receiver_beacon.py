from sqlalchemy.sql import func
from .beacon import Beacon

from app import db


class ReceiverBeacon(Beacon):
    __tablename__ = "receiver_beacons"

    # disable irrelevant aprs fields
    track = None
    ground_speed = None

    # ReceiverBeacon specific data
    version = db.Column(db.String)
    platform = db.Column(db.String)
    cpu_load = db.Column(db.Float(precision=2))
    free_ram = db.Column(db.Float(precision=2))
    total_ram = db.Column(db.Float(precision=2))
    ntp_error = db.Column(db.Float(precision=2))
    rt_crystal_correction = db.Column(db.Float(precision=2))
    voltage = db.Column(db.Float(precision=2))
    amperage = db.Column(db.Float(precision=2))
    cpu_temp = db.Column(db.Float(precision=2))
    senders_visible = db.Column(db.Integer)
    senders_total = db.Column(db.Integer)
    rec_input_noise = db.Column(db.Float(precision=2))
    senders_signal = db.Column(db.Float(precision=2))
    senders_messages = db.Column(db.Integer)
    good_senders_signal = db.Column(db.Float(precision=2))
    good_senders = db.Column(db.Integer)
    good_and_bad_senders = db.Column(db.Integer)

    # User comment: used for additional information like hardware configuration, web site, email address, ...
    user_comment = None

    # Relations
    receiver_id = db.Column(db.Integer, db.ForeignKey("receivers.id", ondelete="SET NULL"))
    receiver = db.relationship("Receiver", foreign_keys=[receiver_id], backref="receiver_beacons")

    # Multi-column indices
    db.Index("ix_receiver_beacons_receiver_id_name", "receiver_id", "name")

    def __repr__(self):
        return "<ReceiverBeacon %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
            self.version,
            self.platform,
            self.cpu_load,
            self.free_ram,
            self.total_ram,
            self.ntp_error,
            self.rt_crystal_correction,
            self.voltage,
            self.amperage,
            self.cpu_temp,
            self.senders_visible,
            self.senders_total,
            self.rec_input_noise,
            self.senders_signal,
            self.senders_messages,
            self.good_senders_signal,
            self.good_senders,
            self.good_and_bad_senders,
        )

    @classmethod
    def get_columns(self):
        return [
            "location",
            "altitude",
            "name",
            "dstcall",
            "receiver_name",
            "timestamp",
            # 'raw_message',
            # 'reference_timestamp',
            "version",
            "platform",
            "cpu_load",
            "free_ram",
            "total_ram",
            "ntp_error",
            "rt_crystal_correction",
            "voltage",
            "amperage",
            "cpu_temp",
            "senders_visible",
            "senders_total",
            "rec_input_noise",
            "senders_signal",
            "senders_messages",
            "good_senders_signal",
            "good_senders",
            "good_and_bad_senders",
        ]

    def get_values(self):
        return [
            self.location_wkt,
            int(self.altitude) if self.altitude else None,
            self.name,
            self.dstcall,
            self.receiver_name,
            self.timestamp,
            # self.raw_message,
            # self.reference_timestamp,
            self.version,
            self.platform,
            self.cpu_load,
            self.free_ram,
            self.total_ram,
            self.ntp_error,
            self.rt_crystal_correction,
            self.voltage,
            self.amperage,
            self.cpu_temp,
            int(self.senders_visible) if self.senders_visible else None,
            int(self.senders_total) if self.senders_visible else None,
            self.rec_input_noise,
            self.senders_signal,
            int(self.senders_messages) if self.senders_messages else None,
            self.good_senders_signal,
            int(self.good_senders) if self.good_senders else None,
            int(self.good_and_bad_senders) if self.good_and_bad_senders else None,
        ]


db.Index("ix_receiver_beacons_date_receiver_id", func.date(ReceiverBeacon.timestamp), ReceiverBeacon.receiver_id)
