from .model import Beacon, AircraftBeacon, ReceiverBeacon


def parse_aprs(text):
    if not isinstance(text, str):
        raise Exception("Unknown type: %s" % type(text))
    elif text == "":
        raise Exception("String is empty")
    elif text[0] == "#":
        return None

    beacon = Beacon()
    beacon.parse(text)

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
