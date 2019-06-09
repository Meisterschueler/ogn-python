from datetime import datetime, timedelta, timezone, date

from ogn_python.model import AircraftBeacon, Device, Receiver

from ogn_python import db
from ogn_python.model.receiver_beacon import ReceiverBeacon


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def encode(address):
    return 'xx' + address


def decode(code):
    return code[2:9]


def rec(min_timestamp, min_online_timestamp):
    last_seen_query = db.session.query(ReceiverBeacon) \
        .filter(ReceiverBeacon.timestamp > min_timestamp) \
        .order_by(ReceiverBeacon.receiver_id, ReceiverBeacon.timestamp) \
        .distinct(ReceiverBeacon.receiver_id)

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<markers>')
    lines.append('<m e="0"/>')
    for receiver_beacon in last_seen_query:
        if receiver_beacon.location == None or receiver_beacon.name.startswith('FNB'):
            continue
        lines.append('<m a="{0}" b="{1:.7f}" c="{2:.7f}" d="{3:1d}"/>'
                     .format(receiver_beacon.name, receiver_beacon.location.latitude, receiver_beacon.location.longitude, receiver_beacon.timestamp < min_online_timestamp))

    lines.append('</markers>')
    xml = '\n'.join(lines)

    return xml


def lxml(show_offline=False, lat_max=90, lat_min=-90, lon_max=180, lon_min=-180):

    timestamp_range_filter = [db.between(AircraftBeacon.timestamp, datetime(2018, 7, 31, 11, 55, 0), datetime(2018, 7, 31, 12, 5, 0))]

    last_seen_query = db.session.query(AircraftBeacon) \
        .filter(*timestamp_range_filter) \
        .order_by(AircraftBeacon.device_id, AircraftBeacon.timestamp) \
        .distinct(AircraftBeacon.device_id) \

    lines = list()
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<markers>')

    for aircraft_beacon in last_seen_query:
        device = aircraft_beacon.device

        code = encode(device.address)

        if device.info:
            if (not device.info.tracked or not device.info.identified):
                continue

            if not device.info.competition:
                competition = device.info.registration[-2:]
            else:
                competition = device.info.competition

            if not device.info.registration:
                registration = '???'
            else:
                registration = device.info.registration

            address = device.address

        else:
            competition = ('_' + code[-2:]).lower()
            registration = code
            address = 0

        elapsed_time = datetime.utcnow() - aircraft_beacon.timestamp
        elapsed_seconds = int(elapsed_time.total_seconds())

        lines.append('   <m a="{0:.7f},{1:.7f},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13}"/>'
                     .format(aircraft_beacon.location.latitude,
                             aircraft_beacon.location.longitude,
                             competition,
                             registration,
                             int(aircraft_beacon.altitude),
                             utc_to_local(aircraft_beacon.timestamp).strftime("%H:%M:%S"),
                             elapsed_seconds,
                             int(aircraft_beacon.track),
                             int(aircraft_beacon.ground_speed),
                             int(aircraft_beacon.climb_rate * 10) / 10,
                             aircraft_beacon.aircraft_type,
                             aircraft_beacon.receiver_name,
                             address,
                             code))

    lines.append('</markers>')
    xml = '\n'.join(lines)

    return xml