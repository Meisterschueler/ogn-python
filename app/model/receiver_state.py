import enum


class ReceiverState(enum.Enum):
    # lower number == more trustworthy
    OK = 0
    ZOMBIE = 1
    UNKNOWN = 2
    OFFLINE = 3
