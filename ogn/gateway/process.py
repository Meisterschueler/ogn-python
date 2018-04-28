import logging

from mgrs import MGRS
from haversine import haversine

from ogn.commands.dbutils import session
from ogn.model import AircraftBeacon, ReceiverBeacon, Location
from ogn.parser import parse, ParseError
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)
myMGRS = MGRS()


def replace_lonlat_with_wkt(message, reference_receiver=None):
    latitude = message['latitude']
    longitude = message['longitude']

    if reference_receiver is not None:
        message['distance'] = 1000.0 * haversine((reference_receiver['latitude'], reference_receiver['longitude']), (latitude, longitude))

    location = Location(longitude, latitude)
    message['location_wkt'] = location.to_wkt()
    message['location_mgrs'] = myMGRS.toMGRS(latitude, longitude).decode('utf-8')
    del message['latitude']
    del message['longitude']
    return message

previous_message = None
receivers = dict()


def message_to_beacon(raw_message, reference_date, wait_for_brother=False):
    beacon = None
    global previous_message
    global receivers

    if raw_message[0] != '#':
        try:
            message = parse(raw_message, reference_date)
        except NotImplementedError as e:
            logger.error('Received message: {}'.format(raw_message))
            logger.error(e)
            return None
        except ParseError as e:
            logger.error('Received message: {}'.format(raw_message))
            logger.error('Drop packet, {}'.format(e.message))
            return None
        except TypeError as e:
            logger.error('TypeError: {}'.format(raw_message))
            return None
        except Exception as e:
            logger.error(raw_message)
            logger.error(e)
            return None

        # update reference receivers and distance to the receiver
        if message['aprs_type'] == 'position':
            if message['beacon_type'] in ['receiver_beacon', 'aprs_receiver', 'receiver']:
                receivers.update({message['name']: {'latitude': message['latitude'], 'longitude': message['longitude']}})
                message = replace_lonlat_with_wkt(message)
            elif message['beacon_type'] in ['aircraft_beacon', 'aprs_aircraft', 'flarm', 'tracker']:
                reference_receiver = receivers.get(message['receiver_name'])
                message = replace_lonlat_with_wkt(message, reference_receiver=reference_receiver)

        # optional: merge different beacon types
        params = dict()
        if wait_for_brother is True:
            if previous_message is None:
                previous_message = message
                return None
            elif message['name'] == previous_message['name'] and message['timestamp'] == previous_message['timestamp']:
                params = message
                params.update(previous_message)
                params['aprs_type'] = 'merged'
                previous_message = None
            else:
                params = previous_message
                previous_message = message
        else:
            params = message

        # create beacons
        if params['beacon_type'] in ['aircraft_beacon', 'aprs_aircraft', 'flarm', 'tracker']:
            beacon = AircraftBeacon(**params)
        elif params['beacon_type'] in ['receiver_beacon', 'aprs_receiver', 'receiver']:
            beacon = ReceiverBeacon(**params)
        else:
            print("Whoops: what is this: {}".format(params))

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
