import logging
from ogn.commands.dbutils import session
from ogn.model import AircraftBeacon, ReceiverBeacon, Device, Receiver, Location
from ogn.parser import parse_aprs, parse_ogn_receiver_beacon, parse_ogn_aircraft_beacon, ParseError
from ogn.model.address_origin import AddressOrigin

logger = logging.getLogger(__name__)


def replace_lonlat_with_wkt(message):
    location = Location(message['longitude'], message['latitude'])
    message['location_wkt'] = location.to_wkt()
    del message['latitude']
    del message['longitude']
    return message


def process_beacon(raw_message):
    if raw_message[0] == '#':
        return
    try:
        message = parse_aprs(raw_message)

        # symboltable / symbolcodes used by OGN:
        # I&: used as receiver
        # /X: helicopter_rotorcraft
        # /': glider_or_motorglider
        # \^: powered_aircraft
        # /g: para_glider
        # /O: ?
        # /^: ?
        # \n: ?
        # /z: ?
        # /o: ?
        if message['symboltable'] == "I" and message['symbolcode'] == '&':
            # ... we have a receiver_beacon
            message.update(parse_ogn_receiver_beacon(message['comment']))
            message = replace_lonlat_with_wkt(message)
            beacon = ReceiverBeacon(**message)

            # connect beacon with receiver
            receiver = session.query(Receiver.id) \
                .filter(Receiver.name == beacon.name) \
                .first()
            if receiver is None:
                receiver = Receiver()
                receiver.name = beacon.name
                session.add(receiver)
            beacon.receiver_id = receiver.id
        else:
            # ... we have a aircraft_beacon
            message.update(parse_ogn_aircraft_beacon(message['comment']))
            message = replace_lonlat_with_wkt(message)
            beacon = AircraftBeacon(**message)

            # connect beacon with device
            device = session.query(Device.id) \
                .filter(Device.address == beacon.address) \
                .order_by(Device.address_origin) \
                .first()
            if device is None:
                device = Device()
                device.address = beacon.address
                device.address_origin = AddressOrigin.seen
                session.add(device)
            beacon.device_id = device.id

            # connect beacon with receiver
            receiver = session.query(Receiver.id) \
                .filter(Receiver.name == beacon.receiver_name) \
                .first()
            if receiver is None:
                receiver = Receiver()
                receiver.name = beacon.receiver_name
                session.add(receiver)
            beacon.receiver_id = receiver.id

        session.add(beacon)
        session.commit()
        logger.debug('Received message: {}'.format(raw_message))
    except ParseError as e:
        logger.error('Received message: {}'.format(raw_message))
        logger.error('Drop packet, {}'.format(e.message))
    except TypeError as e:
        logger.error('TypeError: {}'.format(raw_message))
