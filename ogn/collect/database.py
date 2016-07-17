from celery.utils.log import get_task_logger

from ogn.model import DeviceInfo, AddressOrigin
from ogn.utils import get_ddb

from ogn.collect.celery import app


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
    address_origin = AddressOrigin.ogn_ddb

    counter = update_device_infos(app.session, address_origin)
    logger.info("Imported {} devices.".format(counter))


@app.task
def import_file(path='tests/custom_ddb.txt'):
    """Import registered devices from a local file."""

    logger.info("Import registered devices from '{}'...".format(path))
    address_origin = AddressOrigin.user_defined

    counter = update_device_infos(app.session, address_origin, csvfile=path)
    logger.info("Imported {} devices.".format(counter))
