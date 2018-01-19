from sqlalchemy import Column, String, Integer, Float, Boolean, SmallInteger, ForeignKey, Index
from sqlalchemy.orm import relationship

from .beacon import Beacon


class AircraftBeacon(Beacon):
    __tablename__ = "aircraft_beacons"

    # Flarm specific data
    address_type = Column(SmallInteger)
    aircraft_type = Column(SmallInteger)
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

    proximity = None
    gps_satellites = None
    gps_quality = None
    gps_altitude = None
    pressure = None
    temperature = None
    humidity = None
    voltage = None
    transmitter_power = None
    noise_level = None
    relays = None

    # Calculated values
    distance = Column(Float)
    location_mgrs = Column(String(15), index=True)

    # Relations
    receiver_id = Column(Integer, ForeignKey('receivers.id', ondelete='SET NULL'))
    receiver = relationship('Receiver', foreign_keys=[receiver_id], backref='aircraft_beacons')

    device_id = Column(Integer, ForeignKey('devices.id', ondelete='SET NULL'))
    device = relationship('Device', foreign_keys=[device_id], backref='aircraft_beacons')

    # Multi-column indices
    Index('ix_aircraft_beacons_receiver_id_receiver_name', 'receiver_id', 'receiver_name')
    Index('ix_aircraft_beacons_device_id_address', 'device_id', 'address')

    def __repr__(self):
        return "<AircraftBeacon %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
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

            self.location_mgrs)

    @classmethod
    def get_csv_columns(self):
        return['location',
               'altitude',
               'name',
               'receiver_name',
               'dstcall',
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
               'signal_power',

               'location_mgrs']

    def get_csv_values(self):
        return [
            self.location_wkt,
            int(self.altitude),
            self.name,
            self.receiver_name,
            self.dstcall,
            self.timestamp,
            self.track,
            self.ground_speed,

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

            self.location_mgrs]
