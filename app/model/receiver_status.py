from app import db


class ReceiverStatus(db.Model):
    __tablename__ = "receiver_statuses"

    reference_timestamp = db.Column(db.DateTime, primary_key=True)

    # APRS data
    name = db.Column(db.String)
    dstcall = db.Column(db.String)
    receiver_name = db.Column(db.String(9))
    timestamp = db.Column(db.DateTime)

    # Type information
    beacon_type = None
    aprs_type = None

    # Debug information
    raw_message = None

    # Receiver specific data
    version = db.Column(db.String)
    platform = db.Column(db.String)
    cpu_load = None
    free_ram = None
    total_ram = None
    ntp_error = None

    rt_crystal_correction = None
    voltage = None
    amperage = None
    cpu_temp = db.Column(db.Float(precision=2))
    senders_visible = None
    senders_total = None
    rec_crystal_correction = None
    rec_crystal_correction_fine = None
    rec_input_noise = db.Column(db.Float(precision=2))
    senders_signal = None
    senders_messages = None
    good_senders_signal = None
    good_senders = None
    good_and_bad_senders = None

    # Calculated values (from this software)
    location_mgrs = db.Column(db.String(15))                # full mgrs (15 chars)
    location_mgrs_short = db.Column(db.String(9))           # reduced mgrs (9 chars), e.g. used for melissas range tool
    agl = db.Column(db.Float(precision=2))
