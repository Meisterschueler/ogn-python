import enum


class SenderInfoOrigin(enum.Enum):
    # lower number == more trustworthy
    USER_DEFINED = 0
    OGN_DDB = 1
    FLARMNET = 2
    UNKNOWN = 3
