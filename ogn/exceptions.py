"""
exception definitions
"""


class AprsParseError(Exception):
    """Parse error while parsing an aprs packet."""
    def __init__(self, aprs_string):
        self.message = "This is not a valid APRS string: %s" % aprs_string
        super(AprsParseError, self).__init__(self.message)
        self.aprs_string = aprs_string


class OgnParseError(Exception):
    """Parse error while parsing an aprs packet substring"""
    def __init__(self, substring, expected_type):
        self.message = "For type %s this is not a valid token: %s" % (expected_type, substring)
        super(OgnParseError, self).__init__(self.message)
        self.substring = substring
        self.expected_type = expected_type
