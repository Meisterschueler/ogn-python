from datetime import datetime, timedelta
from ogn.model import AircraftBeacon, ReceiverBeacon

AIRCRAFT_TYPES = ['aprs_aircraft', 'flarm', 'tracker', 'fanet', 'lt24', 'naviter', 'skylines', 'spider', 'spot']
RECEIVER_TYPES = ['aprs_receiver', 'receiver']


class DummyMerger:
    def __init__(self, callback):
        self.callback = callback

    def add_message(self, message):
        self.callback.add_message(message)

    def flush(self):
        pass


class Merger:
    def __init__(self, callback, max_timedelta=None, max_lines=None):
        self.callback = callback
        self.max_timedelta = max_timedelta
        self.max_lines = max_lines
        self.message_map = dict()

    def add_message(self, message):
        if message is None or ('raw_message' in message and message['raw_message'][0] == '#'):
            return

        # release old messages
        if self.max_timedelta is not None:
            for receiver, v1 in self.message_map.items():
                for name, v2 in v1.items():
                    for timestamp,message in v2.items():
                        if message['timestamp'] - timestamp > self.max_timedelta:
                            self.callback.add_message(message)
                            del self.message_map[receiver][name][timestamp]

        # release messages > max_lines
        if self.max_lines is not None:
            pass

        # merge messages with same timestamp
        receiver_name = message['receiver_name']
        name = message['name']
        timestamp = message['timestamp']

        if receiver_name in self.message_map:
            if name in self.message_map[receiver_name]:
                timestamps = self.message_map[receiver_name][name]
                if timestamp in timestamps:
                    other = timestamps[timestamp]
                    params1 = dict([(k, v) for k, v in message.items() if v is not None])
                    params2 = dict([(k, v) for k, v in other.items() if v is not None])
                    merged = {**params1, **params2}

                    # zum debuggen
                    if 'raw_message' in message and 'raw_message' in other:
                        merged['raw_message'] = '"{}","{}"'.format(message['raw_message'], other['raw_message'])

                    self.callback.add_message(merged)
                    del self.message_map[receiver_name][name][timestamp]
                else:
                    self.message_map[receiver_name][name][timestamp] = message

                # release previous messages
                for ts in list(timestamps):
                    if ts < timestamp:
                        self.callback.add_message(timestamps[ts])
                        del self.message_map[receiver_name][name][ts]
            else:
                # add new message
                self.message_map[receiver_name].update({name: {timestamp: message}})
        else:
            self.message_map.update({receiver_name: {name: {timestamp: message}}})

    def flush(self):
        for receiver, v1 in self.message_map.items():
            for name, v2 in v1.items():
                for timestamp in v2:
                    self.callback.add_message(self.message_map[receiver][name][timestamp])

        self.callback.flush()
        self.message_map = dict()


class Converter:
    def __init__(self, callback):
        self.callback = callback

    def add_message(self, message):
        if message['aprs_type'] in ['status', 'position']:
            beacon = self.message_to_beacon(message)
            self.callback.add_message(beacon)

    def message_to_beacon(self, message):
        # create beacons
        if message['beacon_type'] in AIRCRAFT_TYPES:
            beacon = AircraftBeacon(**message)
        elif message['beacon_type'] in RECEIVER_TYPES:
            if 'rec_crystal_correction' in message:
                del message['rec_crystal_correction']
                del message['rec_crystal_correction_fine']
            beacon = ReceiverBeacon(**message)
        else:
            print("Whoops: what is this: {}".format(message))

        return beacon

    def flush(self):
        self.callback.flush()


class DummySaver:
    def add_message(self, message):
        print(message)

    def flush(self):
        print("========== flush ==========")


class DbSaver:
    def __init__(self, session):
        self.session = session
        self.beacons = list()
        self.last_commit = datetime.utcnow()

    def add_message(self, beacon):
        global last_commit
        global beacons

        self.beacons.append(beacon)

        elapsed_time = datetime.utcnow() - self.last_commit
        if elapsed_time >= timedelta(seconds=1):
            self.flush()

    def flush(self):
        try:
            self.session.bulk_save_objects(self.beacons)
            self.session.commit()
            self.beacons = list()
            self.last_commit = datetime.utcnow()
        except Exception as e:
            self.session.rollback()
            print(e)
            return


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
