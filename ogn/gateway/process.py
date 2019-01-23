import logging

from mgrs import MGRS

from ogn.commands.dbutils import session
from ogn.model import Location
from ogn.parser import parse, ParseError
from ogn.gateway.process_tools import DbSaver, Converter, DummyMerger, AIRCRAFT_TYPES, RECEIVER_TYPES


logger = logging.getLogger(__name__)
myMGRS = MGRS()


def _replace_lonlat_with_wkt(message):
    latitude = message['latitude']
    longitude = message['longitude']

    location = Location(longitude, latitude)
    message['location_wkt'] = location.to_wkt()
    location_mgrs = myMGRS.toMGRS(latitude, longitude).decode('utf-8')
    message['location_mgrs'] = location_mgrs
    message['location_mgrs_short'] = location_mgrs[0:5] + location_mgrs[5:7] + location_mgrs[10:12]
    del message['latitude']
    del message['longitude']
    return message


def string_to_message(raw_string, reference_date):
    global receivers

    try:
        message = parse(raw_string, reference_date)
    except NotImplementedError as e:
        #logger.w('No parser implemented for message: {}'.format(raw_string))
        return None
    except ParseError as e:
        #logger.error('Parsing error with message: {}'.format(raw_string))
        return None
    except TypeError as e:
        #logger.error('TypeError with message: {}'.format(raw_string))
        return None
    except Exception as e:
        #logger.error(raw_string)
        #logger.error(e)
        return None

    # update reference receivers and distance to the receiver
    if message['aprs_type'] == 'position':
        if message['beacon_type'] in RECEIVER_TYPES:
            message = _replace_lonlat_with_wkt(message)
        elif message['beacon_type'] in AIRCRAFT_TYPES:
            message = _replace_lonlat_with_wkt(message)
            if 'gps_quality' in message:
                if message['gps_quality'] is not None and 'horizontal' in message['gps_quality']:
                    message['gps_quality_horizontal'] = message['gps_quality']['horizontal']
                    message['gps_quality_vertical'] = message['gps_quality']['vertical']
                del message['gps_quality']

    # update raw_message
    message['raw_message'] = raw_string

    return message


# Build the processing pipeline
saver = DbSaver(session=session)
converter = Converter(callback=saver)
merger = DummyMerger(callback=converter)


def process_raw_message(raw_message, reference_date=None, merger=merger):
    logger.debug('Received message: {}'.format(raw_message))
    message = string_to_message(raw_message, reference_date)
    merger.add_message(message)


