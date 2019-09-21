import enum


class DeviceInfoOrigin(enum.Enum):
    UNKNOWN = 0
    OGN_DDB = 1
    FLARMNET = 2
    USER_DEFINED = 3
