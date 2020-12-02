from app import db


class FrequencyScanFile(db.Model):
    __tablename__ = "frequency_scan_files"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    gain = db.Column(db.Float(precision=2), nullable=False)
    upload_ip_address = db.Column(db.String, nullable=False)
    upload_timestamp = db.Column(db.DateTime, nullable=False, index=True)

    # Relations
    receiver_id = db.Column(db.Integer, db.ForeignKey("receivers.id", ondelete="CASCADE"), index=True)
    receiver = db.relationship("Receiver", foreign_keys=[receiver_id], backref=db.backref("frequency_scan_files", order_by=upload_timestamp.desc()))

    def __repr__(self):
        return "<FrequencyScanFile: %s,%s,%s>" % (self.name, self.upload_ip_address, self.upload_timestamp)
