from sqlalchemy.sql import null

from celery.utils.log import get_task_logger

from ogn.model import Device, AddressOrigin
from ogn.utils import get_ddb

from ogn.collect.celery import app


logger = get_task_logger(__name__)

temp_address_origin = 7


def add_devices(session, origin):
    before_sq = session.query(Device.address) \
        .filter(Device.address_origin == origin) \
        .subquery()
    add_query = session.query(Device) \
        .filter(Device.address_origin == temp_address_origin) \
        .filter(~Device.address.in_(before_sq))

    result = add_query.update({Device.address_origin: origin},
                              synchronize_session='fetch')

    return result


def update_devices(session, origin, devices):
    session.query(Device) \
        .filter(Device.address_origin == temp_address_origin) \
        .delete()

    session.bulk_save_objects(devices)

    # mark temporary added devices
    session.query(Device) \
        .filter(Device.address_origin == null()) \
        .update({Device.address_origin: temp_address_origin})

    logger.info('Added {} devices'.format(add_devices(session, origin)))

    # delete temporary added devices
    session.query(Device) \
        .filter(Device.address_origin == temp_address_origin) \
        .delete()

    session.commit()

    return len(devices)


@app.task
def import_ddb():
    """Import registered devices from the DDB."""

    logger.info("Import registered devices fom the DDB...")
    counter = update_devices(app.session, AddressOrigin.ogn_ddb, get_ddb())
    logger.info("Imported {} devices.".format(counter))


@app.task
def import_file(path='tests/custom_ddb.txt'):
    """Import registered devices from a local file."""

    logger.info("Import registered devices from '{}'...".format(path))
    counter = update_devices(app.session, AddressOrigin.user_defined,
                             get_ddb(path))
    logger.info("Imported {} devices.".format(counter))
