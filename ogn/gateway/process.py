import logging

from mgrs import MGRS

from ogn.commands.dbutils import session
from ogn.model import AircraftBeacon, ReceiverBeacon, Location
from ogn.parser import parse, ParseError
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)
myMGRS = MGRS()


def replace_lonlat_with_wkt(message, reference_position=None):
    from haversine import haversine

    latitude = message['latitude']
    longitude = message['longitude']

    if reference_position is not None:
        message['distance'] = 1000.0 * haversine((reference_position['latitude'], reference_position['longitude']), (latitude, longitude))

    location = Location(longitude, latitude)
    message['location_wkt'] = location.to_wkt()
    message['location_mgrs'] = myMGRS.toMGRS(latitude, longitude).decode('utf-8')
    del message['latitude']
    del message['longitude']
    return message


def message_to_beacon(raw_message, reference_date, receivers=None):
    beacon = None

    if raw_message[0] != '#':
        try:
            message = parse(raw_message, reference_date)
            if message['aprs_type'] == 'position':
                if message['beacon_type'] == 'receiver_beacon':
                    receivers.update({message['name']: {'latitude': message['latitude'], 'longitude': message['longitude']}})
                    message = replace_lonlat_with_wkt(message)
                elif message['beacon_type'] == 'aircraft_beacon':
                    reference_receiver = receivers.get(message['receiver_name'])
                    message = replace_lonlat_with_wkt(message, reference_position=reference_receiver)

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
        except Exception as e:
            logger.error(raw_message)
            logger.error(e)

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
