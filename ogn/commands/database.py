from sqlalchemy import func, and_, true, false

from ogn.model import Base, AddressOrigin, Device
from ogn.collect.fetchddb import update_ddb_from_ogn, update_ddb_from_file
from ogn.commands.dbutils import engine, session

from manager import Manager
manager = Manager()


@manager.command
def init():
    """Initialize the database."""
    Base.metadata.create_all(engine)
    print("Done.")


@manager.command
def update_ddb_ogn():
    """Update devices with data from ogn."""
    print("Updating ddb data...")
    result = update_ddb_from_ogn.delay()
    counter = result.get()
    print("Imported %i devices." % counter)


@manager.command
def update_ddb_file():
    """Update devices with data from local file."""
    print("Updating ddb data...")
    result = update_ddb_from_file.delay()
    counter = result.get()
    print("Imported %i devices." % counter)


@manager.command
def stats():
    """Show some devices stats."""
    sq_nt = session.query(Device.address) \
        .filter(and_(Device.tracked == false(), Device.identified == true())) \
        .subquery()

    sq_ni = session.query(Device.address) \
        .filter(and_(Device.tracked == true(), Device.identified == false())) \
        .subquery()

    sq_ntni = session.query(Device.address) \
        .filter(and_(Device.tracked == false(), Device.identified == false())) \
        .subquery()

    query = session.query(Device.address_origin, func.count(Device.id), func.count(sq_nt.c.address), func.count(sq_ni.c.address), func.count(sq_ntni.c.address)) \
        .outerjoin(sq_nt, sq_nt.c.address == Device.address) \
        .outerjoin(sq_ni, sq_ni.c.address == Device.address) \
        .outerjoin(sq_ntni, sq_ntni.c.address == Device.address) \
        .group_by(Device.address_origin)

    print('--- Devices ---')
    for [address_origin, device_count, nt_count, ni_count, ntni_count] in query.all():
        print('{:12s} Total:{:5d} - not tracked:{:3d}, not identified:{:3d}, not tracked & not identified: {:3d}'
              .format(AddressOrigin(address_origin).name(),
                      device_count,
                      nt_count,
                      ni_count,
                      ntni_count))
