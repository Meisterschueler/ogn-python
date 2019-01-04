from datetime import datetime, timedelta, timezone, date

from sqlalchemy import func, and_, between, case

from ogn.model import AircraftBeacon, Device, Receiver


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def encode(address):
    return 'xx' + address


def decode(code):
    return code[2:9]


def rec(session):
    last_10_minutes = datetime.utcnow() - timedelta(minutes=10)
    receiver_query = session.query(Receiver,
                                   case([(Receiver.lastseen > last_10_minutes, True)],
                                        else_=False).label('is_online')) \
        .order_by(Receiver.name)

    lines = list()
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<markers>')
    lines.append('<m e="0"/>')
    for [receiver, is_online] in receiver_query.all():
        lines.append('<m a="{0}" b="{1:.7f}" c="{2:.7f}" d="{3:1d}"/>'
                     .format(receiver.name, receiver.location.latitude, receiver.location.longitude, is_online))

    lines.append('</markers>')
    xml = '\n'.join(lines)

    return xml


def lxml(session, show_offline=False, lat_max=90, lat_min=-90, lon_max=180, lon_min=-180):

    if show_offline:
        observation_start = date.today()
    else:
        observation_start = datetime.utcnow() - timedelta(minutes=5)

    position_query = session.query(AircraftBeacon, Device) \
        .filter(and_(between(func.ST_Y(AircraftBeacon.location_wkt), lat_min, lat_max),
                     between(func.ST_X(AircraftBeacon.location_wkt), lon_min, lon_max))) \
        .filter(Device.lastseen > observation_start) \
        .filter(Device.lastseen == AircraftBeacon.timestamp) \
        .filter(Device.id == AircraftBeacon.device_id) \
        .order_by(AircraftBeacon.timestamp)

    lines = list()
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<markers>')

    for [aircraft_beacon, device] in position_query.all():
        code = encode(device.address)

        if len(device.infos) > 0:
            device_info = device.infos[0]
            if device_info and (not device_info.tracked or not device_info.identified):
                continue

            if not device_info.competition:
                competition = device_info.registration[-2:]
            else:
                competition = device_info.competition

            if not device_info.registration:
                registration = '???'
            else:
                registration = device_info.registration

            address = device.address

        else:
            device_info = None
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
