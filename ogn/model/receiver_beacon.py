from sqlalchemy import Column, Float, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .beacon import Beacon


class ReceiverBeacon(Beacon):
    __tablename__ = "receiver_beacon"

    # ReceiverBeacon specific data
    version = Column(String)
    platform = Column(String)
    cpu_load = Column(Float)
    cpu_temp = Column(Float)
    free_ram = Column(Float)
    total_ram = Column(Float)
    ntp_error = Column(Float)
    rt_crystal_correction = Column(Float)

    rec_crystal_correction = 0       # obsolete since 0.2.0
    rec_crystal_correction_fine = 0  # obsolete since 0.2.0
    rec_input_noise = Column(Float)

    # Relations
    receiver_id = Column(Integer, ForeignKey('receiver.id', ondelete='SET NULL'), index=True)
    receiver = relationship('Receiver', foreign_keys=[receiver_id])

    def __repr__(self):
        return "<ReceiverBeacon %s: %s>" % (self.name, self.version)
