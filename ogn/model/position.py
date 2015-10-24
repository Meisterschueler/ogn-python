import re

from sqlalchemy import Column, String, Integer, Float, Boolean, SmallInteger

from ogn.aprs_utils import *
from ogn.model.beacon import Beacon


class Position(Beacon):
    __tablename__ = "position"

    # Flarm specific data
    address_type = Column(SmallInteger)
    aircraft_type = Column(SmallInteger)
    stealth = Column(Boolean)
    address = Column(String, index=True)
    climb_rate = Column(Float)
    turn_rate = Column(Float)
    signal_strength = Column(Float)
    error_count = Column(Integer)
    frequency_offset = Column(Float)
    gps_status = Column(String)

    # Pattern
    address_pattern = re.compile(r"id(\S{2})(\S{6})")
    climb_rate_pattern = re.compile(r"([\+\-]\d+)fpm")
    turn_rate_pattern = re.compile(r"([\+\-]\d+\.\d+)rot")
    signal_strength_pattern = re.compile(r"(\d+\.\d+)dB")
    error_count_pattern = re.compile(r"(\d+)e")
    coordinates_extension_pattern = re.compile(r"\!W(.)(.)!")
    hear_ID_pattern = re.compile(r"hear(\w{4})")
    frequency_offset_pattern = re.compile(r"([\+\-]\d+\.\d+)kHz")
    gps_status_pattern = re.compile(r"gps(\d+x\d+)")

    def __init__(self, beacon=None):
        self.heared_aircraft_IDs = list()

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

    def parse(self, text):
        for part in text.split(' '):
            address_match = self.address_pattern.match(part)
            climb_rate_match = self.climb_rate_pattern.match(part)
            turn_rate_match = self.turn_rate_pattern.match(part)
            signal_strength_match = self.signal_strength_pattern.match(part)
            error_count_match = self.error_count_pattern.match(part)
            coordinates_extension_match = self.coordinates_extension_pattern.match(part)
            hear_ID_match = self.hear_ID_pattern.match(part)
            frequency_offset_match = self.frequency_offset_pattern.match(part)
            gps_status_match = self.gps_status_pattern.match(part)

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
                self.climb_rate = int(climb_rate_match.group(1))*fpm2ms
            elif turn_rate_match is not None:
                self.turn_rate = float(turn_rate_match.group(1))
            elif signal_strength_match is not None:
                self.signal_strength = float(signal_strength_match.group(1))
            elif error_count_match is not None:
                self.error_count = int(error_count_match.group(1))
            elif coordinates_extension_match is not None:
                dlat = int(coordinates_extension_match.group(1)) / 1000
                dlon = int(coordinates_extension_match.group(2)) / 1000

                self.latitude = self.latitude + dlat
                self.longitude = self.longitude + dlon
            elif hear_ID_match is not None:
                self.heared_aircraft_IDs.append(hear_ID_match.group(1))
            elif frequency_offset_match is not None:
                self.frequency_offset = float(frequency_offset_match.group(1))
            elif gps_status_match is not None:
                self.gps_status = gps_status_match.group(1)
            else:
                raise Exception("No valid position description: %s" % part)

    def __repr__(self):
        #return("<Position %s: %s %s %s %s %s %s" % (self.name, self.latitude, self.longitude, self.altitude, self.ground_speed, self.track, self.climb_rate))
        return("<Position %s: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s>" % (self.name, self.address_type, self.aircraft_type, self.timestamp, self.address_type, self.aircraft_type, self.stealth, self.address, self.climb_rate, self.turn_rate, self.signal_strength, self.error_count, self.frequency_offset, self.gps_status))