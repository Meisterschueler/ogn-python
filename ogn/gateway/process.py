import logging
from ogn.commands.dbutils import session
from ogn.model import AircraftBeacon, ReceiverBeacon
from ogn.parser import parse_aprs, parse_ogn_receiver_beacon, parse_ogn_aircraft_beacon, ParseError

logger = logging.getLogger(__name__)


def process_beacon(raw_message):
    if raw_message[0] == '#':
        return
    try:
        message = parse_aprs(raw_message)

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
        if message['symboltable'] == "I" and message['symbolcode'] == '&':
            message.update(parse_ogn_receiver_beacon(message['comment']))
            beacon = ReceiverBeacon(**message)
        else:
            message.update(parse_ogn_aircraft_beacon(message['comment']))
            beacon = AircraftBeacon(**message)
        session.add(beacon)
        session.commit()
        logger.debug('Received message: {}'.format(raw_message))
    except ParseError as e:
        logger.error('Received message: {}'.format(raw_message))
        logger.error('Drop packet, {}'.format(e.message))
