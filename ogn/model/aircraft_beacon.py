from sqlalchemy import Column, String, Integer, Float, Boolean, SmallInteger, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .beacon import Beacon


class AircraftBeacon(Beacon):
    __tablename__ = "aircraft_beacons"

    # Activate relay for AircraftBeacon
    relay = Column(String)

    # Flarm specific data
    address_type = Column(SmallInteger)
    aircraft_type = Column(SmallInteger)
    stealth = Column(Boolean)
    address = Column(String(6))
    climb_rate = Column(Float(precision=2))
    turn_rate = Column(Float(precision=2))
    flightlevel = Column(Float(precision=2))
    signal_quality = Column(Float(precision=2))
    error_count = Column(SmallInteger)
    frequency_offset = Column(Float(precision=2))
    gps_status = Column(String)
    software_version = Column(Float(precision=2))
    hardware_version = Column(SmallInteger)
    real_address = Column(String(6))
    signal_power = Column(Float(precision=2))

    # Not so very important data
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
    status = Column(SmallInteger, default=0)
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
    Index('ix_aircraft_beacons_device_id_timestamp', 'device_id', 'timestamp')

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

            self.distance,
            self.location_mgrs)

    @classmethod
    def get_csv_columns(self):
        return['location',
               'altitude',
               'name',
               'dstcall',
               'relay',
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
               'signal_power',

               'distance',
               'location_mgrs']

    def get_csv_values(self):
        return [
            self.location_wkt,
            int(self.altitude),
            self.name,
            self.dstcall,
            self.relay,
            self.receiver_name,
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

            self.distance,
            self.location_mgrs]


Index('ix_aircraft_beacons_date_receiver_id_distance', func.date(AircraftBeacon.timestamp), AircraftBeacon.receiver_id, AircraftBeacon.distance)