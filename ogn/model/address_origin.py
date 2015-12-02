from enum import Enum, unique


@unique
class AddressOrigin(Enum):
    ogn_ddb = 1
    flarmnet = 2
    userdefined = 3
