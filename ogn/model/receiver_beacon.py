import re

from sqlalchemy import Column, String

from .beacon import Beacon


class ReceiverBeacon(Beacon):
    __tablename__ = "receiver_beacon"

    # ReceiverBeacon specific data
    version = Column(String)
    platform = Column(String)
    cpu_load = 0
    cpu_temp = 0
    free_ram = 0
    total_ram = 0
    ntp_error = 0
    rt_crystal_correction = 0

    rec_crystal_correction = 0
    rec_crystal_correction_fine = 0
    rec_input_noise = 0

    # Pattern
    version_pattern = re.compile(r"v(\d+\.\d+\.\d+)\.?(.+)?")
    cpu_pattern = re.compile(r"CPU:(\d+\.\d+)")
    cpu_temp_pattern = re.compile(r"([\+\-]\d+\.\d+)C")
    ram_pattern = re.compile(r"RAM:(\d+\.\d+)/(\d+\.\d+)MB")
    ntp_pattern = re.compile(r"NTP:(\d+\.\d+)ms/([\+\-]\d+\.\d+)ppm")

    rf_pattern_full = re.compile(r"RF:([\+\-]\d+)([\+\-]\d+\.\d+)ppm/([\+\-]\d+\.\d+)dB")
    rf_pattern_light1 = re.compile(r"RF:([\+\-]\d+\.\d+)dB")
    rf_pattern_light2 = re.compile(r"RF:([\+\-]\d+)([\+\-]\d+\.\d+)ppm")

    def __init__(self, beacon=None):
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
            version_match = self.version_pattern.match(part)
            cpu_match = self.cpu_pattern.match(part)
            cpu_temp_match = self.cpu_temp_pattern.match(part)
            ram_match = self.ram_pattern.match(part)
            ntp_match = self.ntp_pattern.match(part)

            rf_full_match = self.rf_pattern_full.match(part)
            rf_light1_match = self.rf_pattern_light1.match(part)
            rf_light2_match = self.rf_pattern_light2.match(part)

            if version_match is not None:
                self.version = version_match.group(1)
                self.platform = version_match.group(2)
            elif cpu_match is not None:
                self.cpu_load = float(cpu_match.group(1))
            elif cpu_temp_match is not None:
                self.cpu_temp = float(cpu_temp_match.group(1))
            elif ram_match is not None:
                self.free_ram = float(ram_match.group(1))
                self.total_ram = float(ram_match.group(2))
            elif ntp_match is not None:
                self.ntp_error = float(ntp_match.group(1))
                self.rt_crystal_correction = float(ntp_match.group(2))
            elif rf_full_match is not None:
                self.rec_crystal_correction = int(rf_full_match.group(1))
                self.rec_crystal_correction_fine = float(rf_full_match.group(2))
                self.rec_input_noise = float(rf_full_match.group(3))
            elif rf_light1_match is not None:
                self.rec_input_noise = float(rf_light1_match.group(1))
            elif rf_light2_match is not None:
                self.rec_crystal_correction = int(rf_light2_match.group(1))
                self.rec_crystal_correction_fine = float(rf_light2_match.group(2))
            else:
                raise Exception("No valid receiver description: %s" % part)

    def __repr__(self):
        return "<ReceiverBeacon %s: %s>" % (self.name, self.version)
