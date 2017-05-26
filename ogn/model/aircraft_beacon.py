from sqlalchemy import Column, String, Integer, Float, Boolean, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship

from .beacon import Beacon


class AircraftBeacon(Beacon):
    __tablename__ = "aircraft_beacon"

    # Flarm specific data
    address_type = Column(SmallInteger)
    aircraft_type = Column(SmallInteger, index=True)
    stealth = Column(Boolean)
    address = Column(String(6))
    climb_rate = Column(Float)
    turn_rate = Column(Float)
    flightlevel = Column(Float)
    signal_quality = Column(Float)
    error_count = Column(Integer)
    frequency_offset = Column(Float)
    gps_status = Column(String)
    software_version = Column(Float)
    hardware_version = Column(SmallInteger)
    real_address = Column(String(6))
    signal_power = Column(Float)

    status = Column(SmallInteger)

    # Relations
    receiver_id = Column(Integer, ForeignKey('receiver.id', ondelete='SET NULL'), index=True)
    receiver = relationship('Receiver', foreign_keys=[receiver_id])

    device_id = Column(Integer, ForeignKey('device.id', ondelete='SET NULL'), index=True)
    device = relationship('Device', foreign_keys=[device_id])

    def __repr__(self):
        return "<AircraftBeacon %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
            self.address_type,
            self.aircraft_type,
            self.stealth,
            self.address,
            self.climb_rate,
            self.turn_rate,
            self.flightlevel,
            self.signal_quality,
            self.error_count,
            self.frequency_offset,
            self.gps_status,
            self.software_version,
            self.hardware_version,
            self.real_address,
            self.signal_power,

            self.status)

    @classmethod
    def get_csv_columns(self):
        return['location',
               'altitude',
               'name',
               'receiver_name',
               'timestamp',
               'track',
               'ground_speed',

               'address_type',
               'aircraft_type',
               'stealth',
               'address',
               'climb_rate',
               'turn_rate',
               'flightlevel',
               'signal_quality',
               'error_count',
               'frequency_offset',
               'gps_status',
               'software_version',
               'hardware_version',
               'real_address',
               'signal_power']

    def get_csv_values(self):
        return [
            self.location_wkt,
            int(self.altitude),
            self.name,
            self.receiver_name,
            self.timestamp,
            self.track,
            round(self.ground_speed, 1) if self.ground_speed else None,

            self.address_type,
            self.aircraft_type,
            self.stealth,
            self.address,
            round(self.climb_rate, 1) if self.climb_rate else None,
            round(self.turn_rate, 1) if self.turn_rate else None,
            self.flightlevel,
            self.signal_quality,
            int(self.error_count) if self.error_count else None,
            self.frequency_offset,
            self.gps_status,
            self.software_version,
            self.hardware_version,
            self.real_address,
            self.signal_power]
