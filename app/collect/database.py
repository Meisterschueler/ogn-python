from sqlalchemy import distinct
from sqlalchemy.sql import null, and_, func, not_, case
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert
from flask import current_app

from app.model import Country, DeviceInfo, DeviceInfoOrigin, AircraftBeacon, ReceiverBeacon, Device, Receiver
from app.utils import get_ddb, get_flarmnet


def upsert(session, model, rows, update_cols):
    """Insert rows in model. On conflicting update columns if new value IS NOT NULL."""

    table = model.__table__

    stmt = insert(table).values(rows)

    on_conflict_stmt = stmt.on_conflict_do_update(
        index_elements=table.primary_key.columns, set_={k: case([(getattr(stmt.excluded, k) != null(), getattr(stmt.excluded, k))], else_=getattr(model, k)) for k in update_cols}
    )

    # print(compile_query(on_conflict_stmt))
    session.execute(on_conflict_stmt)


def update_device_infos(session, address_origin, path=None):
    if address_origin == DeviceInfoOrigin.flarmnet:
        device_infos = get_flarmnet(fln_file=path)
    else:
        device_infos = get_ddb(csv_file=path)

    session.query(DeviceInfo).filter(DeviceInfo.address_origin == address_origin).delete(synchronize_session="fetch")
    session.commit()

    for device_info in device_infos:
        device_info.address_origin = address_origin

    session.bulk_save_objects(device_infos)
    session.commit()

    return len(device_infos)


def import_ddb(session, logger=None):
    """Import registered devices from the DDB."""

    if logger is None:
        logger = current_app.logger

    logger.info("Import registered devices fom the DDB...")
    counter = update_device_infos(session, DeviceInfoOrigin.ogn_ddb)

    finish_message = "DeviceInfo: {} inserted.".format(counter)
    logger.info(finish_message)
    return finish_message


def update_country_code(session, logger=None):
    """Update country code in receivers table if None."""

    if logger is None:
        logger = current_app.logger

    update_receivers = (
        session.query(Receiver)
        .filter(and_(Receiver.country_id == null(), Receiver.location_wkt != null(), func.st_within(Receiver.location_wkt, Country.geom)))
        .update({Receiver.country_id: Country.gid}, synchronize_session="fetch")
    )

    session.commit()

    finish_message = "Receivers (country): {} updated".format(update_receivers)
    logger.info(finish_message)
    return finish_message
