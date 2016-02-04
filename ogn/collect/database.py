from celery.utils.log import get_task_logger

from ogn.model import Device, AddressOrigin
from ogn.utils import get_ddb

from ogn.collect.celery import app


logger = get_task_logger(__name__)


def update_devices(session, origin, devices):
    session.query(Device) \
        .filter(Device.address_origin == origin) \
        .delete()

    session.bulk_save_objects(devices)
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
    counter = update_devices(app.session, AddressOrigin.user_defined, get_ddb(path))
    logger.info("Imported {} devices.".format(counter))
