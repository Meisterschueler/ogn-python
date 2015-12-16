from datetime import datetime

from .model import Beacon, AircraftBeacon, ReceiverBeacon
from ogn.exceptions import AprsParseError


def parse_aprs(packet, reference_date=None):
    if reference_date is None:
        reference_date = datetime.utcnow()
    if not isinstance(packet, str):
        raise TypeError("Expected packet to be str, got %s" % type(packet))
    elif packet == "":
        raise AprsParseError("(empty string)")
    elif packet[0] == "#":
        return None

    beacon = Beacon()
    beacon.parse(packet, reference_date)

    # symboltable / symbolcodes used by OGN:
    # I&: used as receiver
    # /X: helicopter_rotorcraft
    # /': glider_or_motorglider
    # \^: powered_aircraft
    # /g: para_glider
    # /O: ?
    # /^: ?
    # \n: ?
    # /z: ?
    # /o: ?

    if beacon.symboltable == "I" and beacon.symbolcode == "&":
        return ReceiverBeacon(beacon)
    else:
        return AircraftBeacon(beacon)
