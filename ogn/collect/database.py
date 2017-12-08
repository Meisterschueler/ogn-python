from celery.utils.log import get_task_logger

from sqlalchemy import insert, distinct
from sqlalchemy.sql import null, and_, or_, func, not_
from sqlalchemy.sql.expression import case

from ogn.model import DeviceInfo, DeviceInfoOrigin, AircraftBeacon, ReceiverBeacon, Device, Receiver
from ogn.utils import get_ddb, get_country_code

from .celery import app

logger = get_task_logger(__name__)


def update_device_infos(session, address_origin, csvfile=None):
    device_infos = get_ddb(csvfile=csvfile, address_origin=address_origin)

    session.query(DeviceInfo) \
        .filter(DeviceInfo.address_origin == address_origin) \
        .delete()

    session.bulk_save_objects(device_infos)
    session.commit()

    return len(device_infos)


@app.task
def import_ddb():
    """Import registered devices from the DDB."""

    logger.info("Import registered devices fom the DDB...")
    address_origin = DeviceInfoOrigin.ogn_ddb

    counter = update_device_infos(app.session, address_origin)
    logger.info("Imported {} devices.".format(counter))


@app.task
def import_file(path='tests/custom_ddb.txt'):
    """Import registered devices from a local file."""

    logger.info("Import registered devices from '{}'...".format(path))
    address_origin = DeviceInfoOrigin.user_defined

    counter = update_device_infos(app.session, address_origin, csvfile=path)
    logger.info("Imported {} devices.".format(counter))


@app.task
def update_devices():
    """Add/update entries in devices table and update foreign keys in aircraft beacons."""

    # Create missing Device from AircraftBeacon
    available_devices = app.session.query(Device.address) \
        .subquery()

    missing_devices_query = app.session.query(distinct(AircraftBeacon.address)) \
        .filter(and_(AircraftBeacon.device_id == null(), AircraftBeacon.error_count == 0)) \
        .filter(~AircraftBeacon.address.in_(available_devices))

    ins = insert(Device).from_select([Device.address], missing_devices_query)
    res = app.session.execute(ins)
    insert_count = res.rowcount
    app.session.commit()

    # For each address in the new beacons: get firstseen, lastseen and last values != NULL
    last_valid_values = app.session.query(distinct(AircraftBeacon.address).label('address'),
            func.first_value(AircraftBeacon.timestamp)
                .over(partition_by=AircraftBeacon.address, order_by=case([(AircraftBeacon.timestamp == null(), None), (AircraftBeacon.timestamp != null(), AircraftBeacon.timestamp)]))
                .label('firstseen'),
            func.last_value(AircraftBeacon.timestamp)
                .over(partition_by=AircraftBeacon.address, order_by=case([(AircraftBeacon.timestamp == null(), None), (AircraftBeacon.timestamp != null(), AircraftBeacon.timestamp)]))
                .label('lastseen'),
            func.first_value(AircraftBeacon.aircraft_type)
                .over(partition_by=AircraftBeacon.address, order_by=case([(AircraftBeacon.aircraft_type == null(), None), (AircraftBeacon.aircraft_type != null(), AircraftBeacon.aircraft_type)]))
                .label('aircraft_type'),
            func.first_value(AircraftBeacon.stealth)
                .over(partition_by=AircraftBeacon.address, order_by=case([(AircraftBeacon.stealth == null(), None), (AircraftBeacon.stealth != null(), AircraftBeacon.stealth)]))
                .label('stealth'),
            func.first_value(AircraftBeacon.software_version)
                .over(partition_by=AircraftBeacon.address, order_by=case([(AircraftBeacon.software_version == null(), None), (AircraftBeacon.software_version != null(), AircraftBeacon.software_version)]))
                .label('software_version'),
            func.first_value(AircraftBeacon.hardware_version)
                .over(partition_by=AircraftBeacon.address, order_by=case([(AircraftBeacon.hardware_version == null(), None), (AircraftBeacon.hardware_version != null(), AircraftBeacon.hardware_version)]))
                .label('hardware_version'),
            func.first_value(AircraftBeacon.real_address)
                .over(partition_by=AircraftBeacon.address, order_by=case([(AircraftBeacon.real_address == null(), None), (AircraftBeacon.real_address != null(), AircraftBeacon.real_address)]))
                .label('real_address')) \
            .filter(and_(AircraftBeacon.device_id == null(), AircraftBeacon.error_count == 0)) \
            .subquery()

    update_values = app.session.query(Device.address,
                                  case([(or_(Device.firstseen == null(), Device.firstseen > last_valid_values.c.firstseen), last_valid_values.c.firstseen),
                                        (Device.firstseen <= last_valid_values.c.firstseen, Device.firstseen)]).label('firstseen'),
                                  case([(or_(Device.lastseen == null(), Device.lastseen < last_valid_values.c.lastseen), last_valid_values.c.lastseen),
                                        (Device.lastseen >= last_valid_values.c.lastseen, Device.lastseen)]).label('lastseen'),
                                  case([(or_(Device.aircraft_type == null(), Device.lastseen < last_valid_values.c.lastseen), last_valid_values.c.aircraft_type),
                                        (Device.lastseen >= last_valid_values.c.lastseen, Device.aircraft_type)]).label('aircraft_type'),
                                  case([(or_(Device.stealth == null(), Device.lastseen < last_valid_values.c.lastseen), last_valid_values.c.stealth),
                                        (Device.lastseen >= last_valid_values.c.lastseen, Device.stealth)]).label('stealth'),
                                  case([(or_(Device.software_version == null(), Device.lastseen < last_valid_values.c.lastseen), last_valid_values.c.software_version),
                                        (Device.lastseen >= last_valid_values.c.lastseen, Device.software_version)]).label('software_version'),
                                  case([(or_(Device.hardware_version == null(), Device.lastseen < last_valid_values.c.lastseen), last_valid_values.c.hardware_version),
                                        (Device.lastseen >= last_valid_values.c.lastseen, Device.hardware_version)]).label('hardware_version'),
                                  case([(or_(Device.real_address == null(), Device.lastseen < last_valid_values.c.lastseen), last_valid_values.c.real_address),
                                        (Device.lastseen >= last_valid_values.c.lastseen, Device.real_address)]).label('real_address')) \
                           .filter(Device.address == last_valid_values.c.address) \
                           .subquery()

    update_receivers = app.session.query(Device) \
        .filter(Device.address == update_values.c.address) \
        .update({Device.firstseen: update_values.c.firstseen,
                 Device.lastseen: update_values.c.lastseen,
                 Device.aircraft_type: update_values.c.aircraft_type,
                 Device.stealth: update_values.c.stealth,
                 Device.software_version: update_values.c.software_version,
                 Device.hardware_version: update_values.c.hardware_version,
                 Device.real_address: update_values.c.real_address},
                synchronize_session='fetch')

    # Update relations to aircraft beacons
    upd = app.session.query(AircraftBeacon) \
        .filter(AircraftBeacon.device_id == null()) \
        .filter(AircraftBeacon.address == Device.address) \
        .update({AircraftBeacon.device_id: Device.id},
                synchronize_session='fetch')

    app.session.commit()
    print("Devices: {} inserted, {} updated".format(insert_count, update_receivers))
    print("Updated {} AircraftBeacons".format(upd))


@app.task
def update_receivers():
    """Add/update_receivers entries in receiver table and update receivers foreign keys and distance in aircraft beacons and update foreign keys in receiver beacons."""
    # Create missing Receiver from ReceiverBeacon
    available_receivers = app.session.query(Receiver.name) \
        .subquery()

    missing_receiver_query = app.session.query(distinct(ReceiverBeacon.name)) \
        .filter(ReceiverBeacon.receiver_id == null()) \
        .filter(~ReceiverBeacon.name.in_(available_receivers))

    ins = insert(Receiver).from_select([Receiver.name], missing_receiver_query)
    res = app.session.execute(ins)
    insert_count = res.rowcount

    # For each name in the new beacons: get firstseen, lastseen and last values != NULL
    last_valid_values = app.session.query(distinct(ReceiverBeacon.name).label('name'),
            func.first_value(ReceiverBeacon.timestamp)
                .over(partition_by=ReceiverBeacon.name, order_by=case([(ReceiverBeacon.timestamp == null(), None), (ReceiverBeacon.timestamp != null(), ReceiverBeacon.timestamp)]))
                .label('firstseen'),
            func.last_value(ReceiverBeacon.timestamp)
                .over(partition_by=ReceiverBeacon.name, order_by=case([(ReceiverBeacon.timestamp == null(), None), (ReceiverBeacon.timestamp != null(), ReceiverBeacon.timestamp)]))
                .label('lastseen'),
            func.first_value(ReceiverBeacon.location_wkt)
                .over(partition_by=ReceiverBeacon.name, order_by=case([(ReceiverBeacon.location_wkt == null(), None), (ReceiverBeacon.location_wkt != null(), ReceiverBeacon.location_wkt)]))
                .label('location_wkt'),
            func.first_value(ReceiverBeacon.altitude)
                .over(partition_by=ReceiverBeacon.name, order_by=case([(ReceiverBeacon.altitude == null(), None), (ReceiverBeacon.altitude != null(), ReceiverBeacon.altitude)]))
                .label('altitude'),
            func.first_value(ReceiverBeacon.version)
                .over(partition_by=ReceiverBeacon.name, order_by=case([(ReceiverBeacon.version == null(), None), (ReceiverBeacon.version != null(), ReceiverBeacon.version)]))
                .label('version'),
            func.first_value(ReceiverBeacon.platform)
                .over(partition_by=ReceiverBeacon.name, order_by=case([(ReceiverBeacon.platform == null(), None), (ReceiverBeacon.platform != null(), ReceiverBeacon.platform)]))
                .label('platform')) \
        .filter(ReceiverBeacon.receiver_id == null()) \
        .subquery()

    update_values = app.session.query(Receiver.name,
              case([(or_(Receiver.firstseen == null(), Receiver.firstseen > last_valid_values.c.firstseen), last_valid_values.c.firstseen),
                    (Receiver.firstseen <= last_valid_values.c.firstseen, Receiver.firstseen)]).label('firstseen'),
              case([(or_(Receiver.lastseen == null(), Receiver.lastseen < last_valid_values.c.lastseen), last_valid_values.c.lastseen),
                    (Receiver.firstseen >= last_valid_values.c.firstseen, Receiver.firstseen)]).label('lastseen'),
              case([(or_(Receiver.lastseen == null(), Receiver.lastseen < last_valid_values.c.lastseen), func.ST_Transform(last_valid_values.c.location_wkt, 4326)),
                    (Receiver.lastseen >= last_valid_values.c.lastseen, func.ST_Transform(Receiver.location_wkt, 4326))]).label('location_wkt'),
              case([(or_(Receiver.lastseen == null(), Receiver.lastseen < last_valid_values.c.lastseen), last_valid_values.c.altitude),
                    (Receiver.lastseen >= last_valid_values.c.lastseen, Receiver.altitude)]).label('altitude'),
              case([(or_(Receiver.lastseen == null(), Receiver.lastseen < last_valid_values.c.lastseen), last_valid_values.c.version),
                    (Receiver.lastseen >= last_valid_values.c.lastseen, Receiver.version)]).label('version'),
              case([(or_(Receiver.lastseen == null(), Receiver.lastseen < last_valid_values.c.lastseen), last_valid_values.c.platform),
                    (Receiver.lastseen >= last_valid_values.c.lastseen, Receiver.platform)]).label('platform'),
              case([(or_(Receiver.location_wkt == null(), not_(func.ST_Equals(Receiver.location_wkt, last_valid_values.c.location_wkt))), None),    # set country code to None if location changed
                    (func.ST_Equals(Receiver.location_wkt, last_valid_values.c.location_wkt), Receiver.country_code)]).label('country_code')) \
       .filter(Receiver.name == last_valid_values.c.name) \
       .subquery()

    update_receivers = app.session.query(Receiver) \
        .filter(Receiver.name == update_values.c.name) \
        .update({Receiver.firstseen: update_values.c.firstseen,
                 Receiver.lastseen: update_values.c.lastseen,
                 Receiver.location_wkt: update_values.c.location_wkt,
                 Receiver.altitude: update_values.c.altitude,
                 Receiver.version: update_values.c.version,
                 Receiver.platform: update_values.c.platform,
                 Receiver.country_code: update_values.c.country_code},
                synchronize_session='fetch')

    # Update relations to aircraft beacons
    update_aircraft_beacons = app.session.query(AircraftBeacon) \
        .filter(and_(AircraftBeacon.receiver_id == null(), AircraftBeacon.receiver_name == Receiver.name)) \
        .update({AircraftBeacon.receiver_id: Receiver.id,
                 AircraftBeacon.distance: func.ST_Distance_Sphere(AircraftBeacon.location_wkt, Receiver.location_wkt)},
                synchronize_session='fetch')

    # Update relations to receiver beacons
    update_receiver_beacons = app.session.query(ReceiverBeacon) \
        .filter(and_(ReceiverBeacon.receiver_id == null(), ReceiverBeacon.name == Receiver.name)) \
        .update({ReceiverBeacon.receiver_id: Receiver.id},
                synchronize_session='fetch')

    app.session.commit()

    print("Receivers: {} inserted, {} updated.".format(insert_count, update_receivers))
    print("Updated relations: {} aircraft beacons, {} receiver beacons".format(update_aircraft_beacons, update_receiver_beacons))


@app.task
def update_country_code():
    # update country code if None
    unknown_country_query = app.session.query(Receiver) \
        .filter(Receiver.country_code == null()) \
        .filter(Receiver.location_wkt != null()) \
        .order_by(Receiver.name)

    for receiver in unknown_country_query.all():
        location = receiver.location
        country_code = get_country_code(location.latitude, location.longitude)
        if country_code is not None:
            receiver.country_code = country_code
            print("Updated country_code for {} to {}".format(receiver.name, receiver.country_code))

    app.session.commit()
