from .model.beacon import Beacon
from .model.position import Position
from .model.receiver import Receiver


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
        return Receiver(beacon)
    else:
        return Position(beacon)
