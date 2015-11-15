"""
exception definitions
"""


class AprsParseError(Exception):
    """Parse error while parsing an aprs packet substring."""
    def __init__(self, substring, expected_type):
        self.message = "Aprs Substring can't be parsed as %s." % expected_type
        super(AprsParseError, self).__init__(self.message)
        self.substring = substring
        self.expected_type = expected_type
