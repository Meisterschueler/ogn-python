from celery.utils.log import get_task_logger

from sqlalchemy import insert, distinct
from sqlalchemy.sql import null, and_, or_, func, not_
from sqlalchemy.sql.expression import case

from ogn.collect.celery import app
from ogn.model import DeviceInfo, DeviceInfoOrigin, AircraftBeacon, ReceiverBeacon, Device, Receiver
from ogn.utils import get_ddb, get_country_code


logger = get_task_logger(__name__)


def update_device_infos(session, address_origin, csvfile=None):
    device_infos = get_ddb(csvfile=csvfile, address_origin=address_origin)

    session.query(DeviceInfo) \
        .filter(DeviceInfo.address_origin == address_origin) \
        .delete(synchronize_session='fetch')

    session.bulk_save_objects(device_infos)
    session.commit()

    return len(device_infos)


@app.task
def import_ddb(session=None):
    """Import registered devices from the DDB."""

    if session is None:
        session = app.session

    logger.info("Import registered devices fom the DDB...")
    address_origin = DeviceInfoOrigin.ogn_ddb

    counter = update_device_infos(session, address_origin)
    logger.info("Imported {} devices.".format(counter))

    return "Imported {} devices.".format(counter)


@app.task
def import_ddb_file(session=None, path='tests/custom_ddb.txt'):
    """Import registered devices from a local file."""

    if session is None:
        session = app.session

    logger.info("Import registered devices from '{}'...".format(path))
    address_origin = DeviceInfoOrigin.user_defined

    counter = update_device_infos(session, address_origin, csvfile=path)
    logger.info("Imported {} devices.".format(counter))

    return "Imported {} devices.".format(counter)


@app.task
def update_devices(session=None):
    """Add/update entries in devices table and update foreign keys in aircraft beacons."""

    if session is None:
        session = app.session

    # Create missing Device from AircraftBeacon
    available_devices = session.query(Device.address) \
        .subquery()

    missing_devices_query = session.query(distinct(AircraftBeacon.address)) \
        .filter(and_(AircraftBeacon.device_id == null(), not_(AircraftBeacon.address.like('00%')), AircraftBeacon.error_count == 0)) \
        .filter(~AircraftBeacon.address.in_(available_devices))

    ins = insert(Device).from_select([Device.address], missing_devices_query)
    res = session.execute(ins)
    insert_count = res.rowcount
    session.commit()

    # Update relations to aircraft beacons
    upd = session.query(AircraftBeacon) \
        .filter(AircraftBeacon.device_id == null()) \
        .filter(AircraftBeacon.address == Device.address) \
        .update({
            AircraftBeacon.device_id: Device.id},
            synchronize_session='fetch')

    session.commit()
    logger.info("Devices: {} inserted, {} updated".format(insert_count, update_receivers))
    logger.info("Updated {} AircraftBeacons".format(upd))

    return "{} Devices inserted, {} Devices updated, {} AircraftBeacons updated" \
        .format(insert_count, update_receivers, upd)


@app.task
def update_receivers(session=None):
    """Add/update_receivers entries in receiver table and update receivers foreign keys and distance in aircraft beacons and update foreign keys in receiver beacons."""

    if session is None:
        session = app.session

    # Create missing Receiver from ReceiverBeacon
    available_receivers = session.query(Receiver.name) \
        .subquery()

    missing_receiver_query = session.query(distinct(ReceiverBeacon.name)) \
        .filter(ReceiverBeacon.receiver_id == null()) \
        .filter(~ReceiverBeacon.name.in_(available_receivers))

    ins = insert(Receiver).from_select([Receiver.name], missing_receiver_query)
    res = session.execute(ins)
    insert_count = res.rowcount

    # Update relations to aircraft beacons
    update_aircraft_beacons = session.query(AircraftBeacon) \
        .filter(and_(AircraftBeacon.receiver_id == null(), AircraftBeacon.receiver_name == Receiver.name)) \
        .update({AircraftBeacon.receiver_id: Receiver.id,
                 AircraftBeacon.distance: func.ST_Distance_Sphere(AircraftBeacon.location_wkt, Receiver.location_wkt)},
                synchronize_session='fetch')

    # Update relations to receiver beacons
    update_receiver_beacons = session.query(ReceiverBeacon) \
        .filter(and_(ReceiverBeacon.receiver_id == null(), ReceiverBeacon.name == Receiver.name)) \
        .update({ReceiverBeacon.receiver_id: Receiver.id},
                synchronize_session='fetch')

    session.commit()

    logger.info("Receivers: {} inserted, {} updated.".format(insert_count, update_receivers))
    logger.info("Updated relations: {} aircraft beacons, {} receiver beacons".format(update_aircraft_beacons, update_receiver_beacons))

    return "{} Receivers inserted, {} Receivers updated, {} AircraftBeacons updated, {} ReceiverBeacons updated" \
        .format(insert_count, update_receivers, update_aircraft_beacons, update_receiver_beacons)


@app.task
def update_country_code(session=None):
    """Update country code in receivers table if None."""

    if session is None:
        session = app.session

    unknown_country_query = session.query(Receiver) \
        .filter(Receiver.country_code == null()) \
        .filter(Receiver.location_wkt != null()) \
        .order_by(Receiver.name)

    counter = 0
    for receiver in unknown_country_query.all():
        location = receiver.location
        country_code = get_country_code(location.latitude, location.longitude)
        if country_code is not None:
            receiver.country_code = country_code
            logger.info("Updated country_code for {} to {}".format(receiver.name, receiver.country_code))
            counter += 1

    session.commit()

    return "Updated country_code for {} Receivers".format(counter)
