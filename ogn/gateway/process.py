import logging

from ogn.commands.dbutils import session
from ogn.model import AircraftBeacon, ReceiverBeacon, Location
from ogn.parser import parse, ParseError
from datetime import datetime, timedelta


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
        except NotImplementedError as e:
            logger.error('Received message: {}'.format(raw_message))
            logger.error(e)
        except ParseError as e:
            logger.error('Received message: {}'.format(raw_message))
            logger.error('Drop packet, {}'.format(e.message))
        except TypeError as e:
            logger.error('TypeError: {}'.format(raw_message))

    return beacon

beacons = list()
last_commit = datetime.utcnow()


def process_beacon(raw_message, reference_date=None):
    global beacons
    global last_commit

    beacon = message_to_beacon(raw_message, reference_date)
    if beacon is not None:
        beacons.append(beacon)
        logger.debug('Received message: {}'.format(raw_message))

    current_time = datetime.utcnow()
    elapsed_time = current_time - last_commit
    if elapsed_time >= timedelta(seconds=1):
        session.bulk_save_objects(beacons)
        session.commit()
        logger.debug('Commited beacons')
        beacons = list()
        last_commit = current_time
