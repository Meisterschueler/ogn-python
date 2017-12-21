from datetime import datetime, timedelta, date
import os

from sqlalchemy import func, and_, between, case, null

from ogn.model import AircraftBeacon, DeviceInfo, Device, Receiver


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

    position_query = session.query(Device, AircraftBeacon, DeviceInfo) \
        .filter(and_(between(func.ST_Y(AircraftBeacon.location_wkt), lat_min, lat_max),
                     between(func.ST_X(AircraftBeacon.location_wkt), lon_min, lon_max))) \
        .filter(Device.lastseen > observation_start) \
        .filter(Device.last_position_beacon_id == AircraftBeacon.id) \
        .outerjoin(DeviceInfo, DeviceInfo.device_id == Device.id)

    lines = list()
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<markers>')

    for [aircraft_beacon, device_info] in position_query.all():
        if device_info and (not device_info.tracked or not device_info.identified):
            continue

        code = encode(aircraft_beacon.address)

        if device_info is None:
            competition = ('_' + code[-2:]).lower()
            registration = code
            address = 0
        else:
            if not device_info.competition:
                competition = device_info.registration[-2:]
            else:
                competition = device_info.competition

            if not device_info.registration:
                registration = '???'
            else:
                registration = device_info.registration

            address = device_info.address

        elapsed_time = datetime.utcnow() - aircraft_beacon.timestamp
        elapsed_seconds = int(elapsed_time.total_seconds())

        lines.append('<m a="{0:.7f},{1:.7f},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13}"/>'
                     .format(aircraft_beacon.location.latitude,
                             aircraft_beacon.location.longitude,
                             competition,
                             registration,
                             aircraft_beacon.altitude,
                             utc_to_local(aircraft_beacon.timestamp).strftime("%H:%M:%S"),
                             elapsed_seconds,
                             int(aircraft_beacon.track),
                             int(aircraft_beacon.ground_speed),
                             int(aircraft_beacon.climb_rate*10)/10,
                             aircraft_beacon.aircraft_type,
                             aircraft_beacon.receiver_name,
                             address,
                             code))

    lines.append('</markers>')
    xml = '\n'.join(lines)

    return xml
