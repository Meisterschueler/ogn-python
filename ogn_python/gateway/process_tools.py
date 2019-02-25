from datetime import datetime, timedelta
from ogn.parser import parse, ParseError
from ogn_python.model import AircraftBeacon, ReceiverBeacon, Location
from ogn_python.collect.database import upsert

from mgrs import MGRS


# define message types we want to proceed
AIRCRAFT_BEACON_TYPES = ['aprs_aircraft', 'flarm', 'tracker', 'fanet', 'lt24', 'naviter', 'skylines', 'spider', 'spot']
RECEIVER_BEACON_TYPES = ['aprs_receiver', 'receiver']

# define fields we want to proceed
BEACON_KEY_FIELDS = ['name', 'receiver_name', 'timestamp']
AIRCRAFT_BEACON_FIELDS = ['location', 'altitude', 'dstcall', 'relay', 'track', 'ground_speed', 'address_type', 'aircraft_type', 'stealth', 'address', 'climb_rate', 'turn_rate', 'signal_quality', 'error_count', 'frequency_offset', 'gps_quality_horizontal', 'gps_quality_vertical', 'software_version', 'hardware_version', 'real_address', 'signal_power', 'distance', 'radial', 'quality', 'location_mgrs', 'location_mgrs_short', 'agl', 'receiver_id', 'device_id']
RECEIVER_BEACON_FIELDS = ['location', 'altitude', 'dstcall', 'relay', 'version', 'platform', 'cpu_load', 'free_ram', 'total_ram', 'ntp_error', 'rt_crystal_correction', 'voltage', 'amperage', 'cpu_temp', 'senders_visible', 'senders_total', 'rec_input_noise', 'senders_signal', 'senders_messages', 'good_senders_signal', 'good_senders', 'good_and_bad_senders']


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
        print('No parser implemented for message: {}'.format(raw_string))
        return None
    except ParseError as e:
        print('Parsing error with message: {}'.format(raw_string))
        return None
    except TypeError as e:
        print('TypeError with message: {}'.format(raw_string))
        return None
    except Exception as e:
        print(raw_string)
        print(e)
        return None

    # update reference receivers and distance to the receiver
    if message['aprs_type'] == 'position':
        if message['beacon_type'] in AIRCRAFT_BEACON_TYPES + RECEIVER_BEACON_TYPES:
            message = _replace_lonlat_with_wkt(message)

        if message['beacon_type'] in AIRCRAFT_BEACON_TYPES and 'gps_quality' in message:
            if message['gps_quality'] is not None and 'horizontal' in message['gps_quality']:
                message['gps_quality_horizontal'] = message['gps_quality']['horizontal']
                message['gps_quality_vertical'] = message['gps_quality']['vertical']
            del message['gps_quality']

    # update raw_message
    message['raw_message'] = raw_string

    return message


class DbSaver:
    def __init__(self, session):
        self.session = session
        self.aircraft_message_map = dict()
        self.receiver_message_map = dict()
        self.last_commit = datetime.utcnow()

    def _put_in_map(self, message, my_map):
        key = message['name'] + message['receiver_name'] + message['timestamp'].strftime('%s')

        if key in my_map:
            other = my_map[key]
            merged = {k: message[k] if message[k] is not None else other[k] for k in message.keys()}
            my_map[key] = merged
        else:
            my_map[key] = message

    def add_raw_message(self, raw_string, reference_date=None):
        if not reference_date:
            reference_date=datetime.utcnow()
        message = string_to_message(raw_string, reference_date=reference_date)
        if message is not None:
            self.add_message(message)
        else:
            print(raw_string)

    def add_message(self, message):
        if message is None or ('raw_message' in message and message['raw_message'][0] == '#') or 'beacon_type' not in message:
            return

        if 'location_wkt' in message:
            message['location'] = message.pop('location_wkt')   # total_time_wasted_here = 3

        if message['beacon_type'] in AIRCRAFT_BEACON_TYPES:
            complete_message = {k: message[k] if k in message else None for k in BEACON_KEY_FIELDS + AIRCRAFT_BEACON_FIELDS}
            self._put_in_map(message=complete_message, my_map=self.aircraft_message_map)
        elif message['beacon_type'] in RECEIVER_BEACON_TYPES:
            complete_message = {k: message[k] if k in message else None for k in BEACON_KEY_FIELDS + RECEIVER_BEACON_FIELDS}
            self._put_in_map(message=complete_message, my_map=self.receiver_message_map)
        else:
            print("Ignore beacon_type: {}".format(message['beacon_type']))
            return

        elapsed_time = datetime.utcnow() - self.last_commit
        if elapsed_time >= timedelta(seconds=5):
            self.flush()

    def flush(self):
        if len(self.aircraft_message_map) > 0:
            messages = list(self.aircraft_message_map.values())
            upsert(session=self.session, model=AircraftBeacon, rows=messages, update_cols=AIRCRAFT_BEACON_FIELDS)
        if len(self.receiver_message_map) > 0:
            messages = list(self.receiver_message_map.values())
            upsert(session=self.session, model=ReceiverBeacon, rows=messages, update_cols=RECEIVER_BEACON_FIELDS)
        self.session.commit()

        self.aircraft_message_map = dict()
        self.receiver_message_map = dict()
        self.last_commit = datetime.utcnow()


import os, gzip, csv


class FileSaver:
    def __init__(self):
        self.aircraft_messages = list()
        self.receiver_messages = list()

    def open(self, path, reference_date_string):
        aircraft_beacon_filename = os.path.join(path, 'aircraft_beacons.csv_' + reference_date_string + '.gz')
        receiver_beacon_filename = os.path.join(path, 'receiver_beacons.csv_' + reference_date_string + '.gz')

        if not os.path.exists(aircraft_beacon_filename) and not os.path.exists(receiver_beacon_filename):
            self.fout_ab = gzip.open(aircraft_beacon_filename, 'wt')
            self.fout_rb = gzip.open(receiver_beacon_filename, 'wt')
        else:
            raise FileExistsError

        self.aircraft_writer = csv.writer(self.fout_ab, delimiter=',')
        self.aircraft_writer.writerow(AircraftBeacon.get_columns())

        self.receiver_writer = csv.writer(self.fout_rb, delimiter=',')
        self.receiver_writer.writerow(ReceiverBeacon.get_columns())

        return 1

    def add_message(self, beacon):
        if isinstance(beacon, AircraftBeacon):
            self.aircraft_messages.append(beacon.get_values())
        elif isinstance(beacon, ReceiverBeacon):
            self.receiver_messages.append(beacon.get_values())

    def flush(self):
        self.aircraft_writer.writerows(self.aircraft_messages)
        self.receiver_writer.writerows(self.receiver_messages)
        self.aircraft_messages = list()
        self.receiver_messages = list()

    def close(self):
        self.fout_ab.close()
        self.fout_rb.close()
