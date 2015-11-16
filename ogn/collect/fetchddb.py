from __future__ import absolute_import

from celery.utils.log import get_task_logger
from ogn.collect.celery import app

from ogn.model import Device
from ogn.utils import get_ddb

logger = get_task_logger(__name__)


@app.task
def update_ddb_data():
    logger.info("Update ddb data.")

    app.session.query(Device).delete()

    devices = get_ddb()
    logger.debug("New Devices: %s" % str(devices))

    app.session.bulk_save_objects(devices)
    app.session.commit()

    return len(devices)


@app.task
def import_ddb_data(filename='custom_ddb.txt'):
    logger.info("Import ddb data from file.")

    devices = get_ddb(filename)

    app.session.bulk_save_objects(devices)
    app.session.commit()

    return len(devices)
