import re

from sqlalchemy import Column, String, Integer, Float, Boolean, SmallInteger

from ogn.parser.utils import fpm2ms
from .beacon import Beacon
from ogn.exceptions import OgnParseError


class AircraftBeacon(Beacon):
    __tablename__ = "aircraft_beacon"

    # Flarm specific data
    address_type = Column(SmallInteger)
    aircraft_type = Column(SmallInteger)
    stealth = Column(Boolean)
    address = Column(String(6), index=True)
    climb_rate = Column(Float)
    turn_rate = Column(Float)
    signal_strength = Column(Float)
    error_count = Column(Integer)
    frequency_offset = Column(Float)
    gps_status = Column(String)

    software_version = Column(Float)
    hardware_version = Column(SmallInteger)
    real_address = Column(String(6))

    flightlevel = Column(Float)

    # Calculated values
    radius = Column(Float)
    theta = Column(Float)
    phi = Column(Float)

    flight_state = Column(SmallInteger)

    # Pattern
    address_pattern = re.compile(r"id(\S{2})(\S{6})")
    climb_rate_pattern = re.compile(r"([\+\-]\d+)fpm")
    turn_rate_pattern = re.compile(r"([\+\-]\d+\.\d+)rot")
    signal_strength_pattern = re.compile(r"(\d+\.\d+)dB")
    error_count_pattern = re.compile(r"(\d+)e")
    coordinates_extension_pattern = re.compile(r"\!W(.)(.)!")
    hear_address_pattern = re.compile(r"hear(\w{4})")
    frequency_offset_pattern = re.compile(r"([\+\-]\d+\.\d+)kHz")
    gps_status_pattern = re.compile(r"gps(\d+x\d+)")

    software_version_pattern = re.compile(r"s(\d+\.\d+)")
    hardware_version_pattern = re.compile(r"h(\d+)")
    real_address_pattern = re.compile(r"r(\w{6})")

    flightlevel_pattern = re.compile(r"FL(\d{3}\.\d{2})")

    def __init__(self, beacon=None):
        self.heared_aircraft_addresses = list()

        if beacon is not None:
            self.name = beacon.name
            self.receiver_name = beacon.receiver_name
            self.timestamp = beacon.timestamp
            self.latitude = beacon.latitude
            self.longitude = beacon.longitude
            self.ground_speed = beacon.ground_speed
            self.track = beacon.track
            self.altitude = beacon.altitude
            self.comment = beacon.comment

            self.parse(beacon.comment)
        else:
            self.latitude = 0.0
            self.longitude = 0.0

    def parse(self, text):
        for part in text.split(' '):
            address_match = self.address_pattern.match(part)
            climb_rate_match = self.climb_rate_pattern.match(part)
            turn_rate_match = self.turn_rate_pattern.match(part)
            signal_strength_match = self.signal_strength_pattern.match(part)
            error_count_match = self.error_count_pattern.match(part)
            coordinates_extension_match = self.coordinates_extension_pattern.match(part)
            hear_address_match = self.hear_address_pattern.match(part)
            frequency_offset_match = self.frequency_offset_pattern.match(part)
            gps_status_match = self.gps_status_pattern.match(part)

            software_version_match = self.software_version_pattern.match(part)
            hardware_version_match = self.hardware_version_pattern.match(part)
            real_address_match = self.real_address_pattern.match(part)

            flightlevel_match = self.flightlevel_pattern.match(part)

            if address_match is not None:
                # Flarm ID type byte in APRS msg: PTTT TTII
                # P => stealth mode
                # TTTTT => aircraftType
                # II => IdType: 0=Random, 1=ICAO, 2=FLARM, 3=OGN
                # (see https://groups.google.com/forum/#!msg/openglidernetwork/lMzl5ZsaCVs/YirmlnkaJOYJ).
                self.address_type = int(address_match.group(1), 16) & 0b00000011
                self.aircraft_type = (int(address_match.group(1), 16) & 0b01111100) >> 2
                self.stealth = ((int(address_match.group(1), 16) & 0b10000000) >> 7 == 1)
                self.address = address_match.group(2)
            elif climb_rate_match is not None:
                self.climb_rate = int(climb_rate_match.group(1)) * fpm2ms
            elif turn_rate_match is not None:
                self.turn_rate = float(turn_rate_match.group(1))
            elif signal_strength_match is not None:
                self.signal_strength = float(signal_strength_match.group(1))
            elif error_count_match is not None:
                self.error_count = int(error_count_match.group(1))
            elif coordinates_extension_match is not None:
                dlat = int(coordinates_extension_match.group(1)) / 1000 / 60
                dlon = int(coordinates_extension_match.group(2)) / 1000 / 60

                self.latitude = self.latitude + dlat
                self.longitude = self.longitude + dlon
            elif hear_address_match is not None:
                self.heared_aircraft_addresses.append(hear_address_match.group(1))
            elif frequency_offset_match is not None:
                self.frequency_offset = float(frequency_offset_match.group(1))
            elif gps_status_match is not None:
                self.gps_status = gps_status_match.group(1)

            elif software_version_match is not None:
                self.software_version = float(software_version_match.group(1))
            elif hardware_version_match is not None:
                self.hardware_version = int(hardware_version_match.group(1))
            elif real_address_match is not None:
                self.real_address = real_address_match.group(1)

            elif flightlevel_match is not None:
                self.flightlevel = float(flightlevel_match.group(1))
            else:
                raise OgnParseError(expected_type="AircraftBeacon", substring=part)

    def __repr__(self):
        return "<AircraftBeacon %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (
            self.name,
            self.address_type,
            self.aircraft_type,
            self.timestamp,
            self.address_type,
            self.aircraft_type,
            self.stealth,
            self.address,
            self.climb_rate,
            self.turn_rate,
            self.signal_strength,
            self.error_count,
            self.frequency_offset,
            self.gps_status)
