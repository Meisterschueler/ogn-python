from sqlalchemy import distinct
from sqlalchemy.sql import null, and_, func, not_, case
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert

from ogn_python.model import Country, DeviceInfo, DeviceInfoOrigin, AircraftBeacon, ReceiverBeacon, Device, Receiver
from ogn_python.utils import get_ddb, get_flarmnet

from ogn_python import app


def update_device_infos(session, address_origin, path=None):
    if address_origin == DeviceInfoOrigin.flarmnet:
        device_infos = get_flarmnet(fln_file=path)
    else:
        device_infos = get_ddb(csv_file=path)

    session.query(DeviceInfo) \
        .filter(DeviceInfo.address_origin == address_origin) \
        .delete(synchronize_session='fetch')
    session.commit()

    for device_info in device_infos:
        device_info.address_origin = address_origin

    session.bulk_save_objects(device_infos)
    session.commit()

    return len(device_infos)


def import_ddb(session, logger=None):
    """Import registered devices from the DDB."""

    if logger is None:
        logger = app.logger

    logger.info("Import registered devices fom the DDB...")
    counter = update_device_infos(session, DeviceInfoOrigin.ogn_ddb)
    logger.info("Imported {} devices.".format(counter))

    return "Imported {} devices.".format(counter)


def update_country_code(session, logger=None):
    """Update country code in receivers table if None."""

    if logger is None:
        logger = app.logger

    update_receivers = session.query(Receiver) \
        .filter(and_(Receiver.country_id == null(), Receiver.location_wkt != null(), func.st_within(Receiver.location_wkt, Country.geom))) \
        .update({Receiver.country_id: Country.gid},
                synchronize_session='fetch')

    session.commit()
    logger.info("Updated {} AircraftBeacons".format(update_receivers))

    return "Updated country for {} Receivers".format(update_receivers)
