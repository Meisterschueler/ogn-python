import logging

from ogn.commands.dbutils import session
from ogn.model import AircraftBeacon, ReceiverBeacon, Location
from ogn.parser import parse, ParseError


logger = logging.getLogger(__name__)


def replace_lonlat_with_wkt(message):
    location = Location(message['longitude'], message['latitude'])
    message['location_wkt'] = location.to_wkt()
    del message['latitude']
    del message['longitude']
    return message


def message_to_beacon(raw_message, reference_date):
    beacon = None

    if raw_message[0] != '#':
        try:
            message = parse(raw_message, reference_date)
            if message['aprs_type'] == 'position':
                message = replace_lonlat_with_wkt(message)

            if message['beacon_type'] == 'aircraft_beacon':
                beacon = AircraftBeacon(**message)
            elif message['beacon_type'] == 'receiver_beacon':
                beacon = ReceiverBeacon(**message)
            else:
                print("Whoops: what is this: {}".format(message))
        except ParseError as e:
            logger.error('Received message: {}'.format(raw_message))
            logger.error('Drop packet, {}'.format(e.message))
        except TypeError as e:
            logger.error('TypeError: {}'.format(raw_message))

    return beacon


def process_beacon(raw_message, reference_date=None):
    beacon = message_to_beacon(raw_message, reference_date)
    if beacon is not None:
        session.add(beacon)
        session.commit()
        logger.debug('Received message: {}'.format(raw_message))
