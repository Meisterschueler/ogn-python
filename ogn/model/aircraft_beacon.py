from sqlalchemy import Column, String, Integer, Float, Boolean, SmallInteger, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .beacon import Beacon


class AircraftBeacon(Beacon):
    __tablename__ = "aircraft_beacons"

    # Flarm specific data
    address_type = Column(SmallInteger)
    aircraft_type = Column(SmallInteger)
    stealth = Column(Boolean)
    address = Column(String)
    climb_rate = Column(Float(precision=2))
    turn_rate = Column(Float(precision=2))
    signal_quality = Column(Float(precision=2))
    error_count = Column(SmallInteger)
    frequency_offset = Column(Float(precision=2))
    gps_quality_horizontal = Column(SmallInteger)
    gps_quality_vertical = Column(SmallInteger)
    software_version = Column(Float(precision=2))
    hardware_version = Column(SmallInteger)
    real_address = Column(String(6))
    signal_power = Column(Float(precision=2))
    proximity = None

    # Calculated values
    distance = Column(Float(precision=2))
    radial = Column(SmallInteger)
    quality = Column(Float(precision=2))    # signal quality normalized to 10km
    location_mgrs = Column(String(15))
    agl = Column(Float(precision=2))

    # Relations
    receiver_id = Column(Integer, ForeignKey('receivers.id', ondelete='SET NULL'))
    receiver = relationship('Receiver', foreign_keys=[receiver_id], backref='aircraft_beacons')

    device_id = Column(Integer, ForeignKey('devices.id', ondelete='SET NULL'))
    device = relationship('Device', foreign_keys=[device_id], backref='aircraft_beacons')

    # Multi-column indices
    Index('ix_aircraft_beacons_receiver_id_distance', 'receiver_id', 'distance')
    Index('ix_aircraft_beacons_device_id_timestamp', 'device_id', 'timestamp')

    def __repr__(self):
        return "<AircraftBeacon %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
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
            self.location_mgrs)

    @classmethod
    def get_columns(self):
        return ['location',
                'altitude',
                'name',
                'dstcall',
                'relay',
                'receiver_name',
                'timestamp',
                'track',
                'ground_speed',
                
                #'raw_message',
                #'reference_timestamp',
                
                'address_type',
                'aircraft_type',
                'stealth',
                'address',
                'climb_rate',
                'turn_rate',
                'signal_quality',
                'error_count',
                'frequency_offset',
                'gps_quality_horizontal',
                'gps_quality_vertical',
                'software_version',
                'hardware_version',
                'real_address',
                'signal_power',
                
                'distance',
                'radial',
                'quality',
                'location_mgrs']

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
            
            #self.raw_message,
            #self.reference_timestamp,

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
            self.location_mgrs]


Index('ix_aircraft_beacons_date_device_id_address', func.date(AircraftBeacon.timestamp), AircraftBeacon.device_id, AircraftBeacon.address)
Index('ix_aircraft_beacons_date_receiver_id_distance', func.date(AircraftBeacon.timestamp), AircraftBeacon.receiver_id, AircraftBeacon.distance)