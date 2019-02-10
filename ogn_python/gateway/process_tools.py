from datetime import datetime, timedelta
from ogn_python.model import AircraftBeacon, ReceiverBeacon
from ogn_python.collect.database import upsert

# define message types we want to proceed
AIRCRAFT_BEACON_TYPES = ['aprs_aircraft', 'flarm', 'tracker', 'fanet', 'lt24', 'naviter', 'skylines', 'spider', 'spot']
RECEIVER_BEACON_TYPES = ['aprs_receiver', 'receiver']

# define fields we want to proceed
BEACON_KEY_FIELDS = ['name', 'receiver_name', 'timestamp']
AIRCRAFT_BEACON_FIELDS = ['location', 'altitude', 'dstcall', 'relay', 'track', 'ground_speed', 'address_type', 'aircraft_type', 'stealth', 'address', 'climb_rate', 'turn_rate', 'signal_quality', 'error_count', 'frequency_offset', 'gps_quality_horizontal', 'gps_quality_vertical', 'software_version', 'hardware_version', 'real_address', 'signal_power', 'distance', 'radial', 'quality', 'location_mgrs', 'location_mgrs_short', 'agl', 'receiver_id', 'device_id']
RECEIVER_BEACON_FIELDS = ['location', 'altitude', 'dstcall', 'relay', 'version', 'platform', 'cpu_load', 'free_ram', 'total_ram', 'ntp_error', 'rt_crystal_correction', 'voltage', 'amperage', 'cpu_temp', 'senders_visible', 'senders_total', 'rec_input_noise', 'senders_signal', 'senders_messages', 'good_senders_signal', 'good_senders', 'good_and_bad_senders']


class DummyMerger:
    def __init__(self, callback):
        self.callback = callback

    def add_message(self, message):
        self.callback.add_message(message)

    def flush(self):
        pass


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

    def add_message(self, message):
        if message is None or ('raw_message' in message and message['raw_message'][0] == '#') or 'beacon_type' not in message:
            return

        if 'location_wkt' in message:
            message['location'] = message.pop('location_wkt')   # total_time_wasted_here = 3

        if message['beacon_type'] in AIRCRAFT_BEACON_TYPES:
            even_messages = {k: message[k] if k in message else None for k in BEACON_KEY_FIELDS + AIRCRAFT_BEACON_FIELDS}
            self._put_in_map(message=even_messages, my_map=self.aircraft_message_map)
        elif message['beacon_type'] in RECEIVER_BEACON_TYPES:
            even_messages = {k: message[k] if k in message else None for k in BEACON_KEY_FIELDS + RECEIVER_BEACON_FIELDS}
            self._put_in_map(message=even_messages, my_map=self.receiver_message_map)
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


class DummySaver:
    def add_message(self, message):
        print(message)

    def flush(self):
        print("========== flush ==========")


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
