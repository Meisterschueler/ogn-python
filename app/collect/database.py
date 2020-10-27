from sqlalchemy.sql import null, and_, func, case
from sqlalchemy.dialects.postgresql import insert
from flask import current_app

from app import db
from app.model import SenderInfo, SenderInfoOrigin, Receiver
from app.utils import get_ddb, get_flarmnet


def upsert(model, rows, update_cols):
    """Insert rows in model. On conflicting update columns if new value IS NOT NULL."""

    table = model.__table__

    stmt = insert(table).values(rows)

    on_conflict_stmt = stmt.on_conflict_do_update(
        index_elements=table.primary_key.columns, set_={k: case([(getattr(stmt.excluded, k) != null(), getattr(stmt.excluded, k))], else_=getattr(model, k)) for k in update_cols}
    )

    # print(compile_query(on_conflict_stmt))
    return on_conflict_stmt


def update_device_infos(address_origin, path=None):
    if address_origin == SenderInfoOrigin.FLARMNET:
        device_infos = get_flarmnet(fln_file=path)
    else:
        device_infos = get_ddb(csv_file=path)

    db.session.query(SenderInfo).filter(SenderInfo.address_origin == address_origin).delete(synchronize_session="fetch")
    db.session.commit()

    for device_info in device_infos:
        device_info.address_origin = address_origin

    db.session.bulk_save_objects(device_infos)
    db.session.commit()

    return len(device_infos)


def import_ddb(logger=None):
    """Import registered devices from the DDB."""

    if logger is None:
        logger = current_app.logger

    logger.info("Import registered devices fom the DDB...")
    counter = update_device_infos(SenderInfoOrigin.OGN_DDB)

    finish_message = "SenderInfo: {} inserted.".format(counter)
    logger.info(finish_message)
    return finish_message
