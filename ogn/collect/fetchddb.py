from __future__ import absolute_import

from celery.utils.log import get_task_logger
from ogn.collect.celery import app

from ogn.model import Device
from ogn.utils import get_ddb
from ogn.model.address_origin import AddressOrigin

logger = get_task_logger(__name__)


@app.task
def update_ddb_from_ogn():
    logger.info("Update ddb data from ogn.")

    app.session.query(Device) \
        .filter(Device.address_origin == AddressOrigin.ogn_ddb) \
        .delete()

    devices = get_ddb()
    logger.debug("New Devices: %s" % str(devices))

    app.session.bulk_save_objects(devices)
    app.session.commit()

    return len(devices)


@app.task
def update_ddb_from_file():
    logger.info("Import ddb data from file.")

    app.session.query(Device) \
        .filter(Device.address_origin == AddressOrigin.userdefined) \
        .delete()

    devices = get_ddb('ogn/custom_ddb.txt')

    app.session.bulk_save_objects(devices)
    app.session.commit()

    return len(devices)
