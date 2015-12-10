"""
exception definitions
"""
from datetime import datetime


class AprsParseError(Exception):
    """Parse error while parsing an aprs packet."""
    def __init__(self, aprs_string):
        self.aprs_string = aprs_string

        self.message = "This is not a valid APRS string: {}".format(aprs_string)
        super(AprsParseError, self).__init__(self.message)


class OgnParseError(Exception):
    """Parse error while parsing an aprs packet substring."""
    def __init__(self, substring, expected_type):
        self.substring = substring
        self.expected_type = expected_type

        self.message = "For type {} this is not a valid token: {}".format(expected_type, substring)
        super(OgnParseError, self).__init__(self.message)


class AmbigousTimeError(Exception):
    """Timstamp from the past/future, can't fully reconstruct datetime from timestamp."""
    def __init__(self, reference, packet_time):
        self.reference = reference
        self.packet_time = packet_time
        self.timedelta = reference - datetime.combine(reference, packet_time)

        self.message = "Can't reconstruct timstamp, {:.0f}s from past.".format(self.timedelta.total_seconds())
        super(AmbigousTimeError, self).__init__(self.message)
