from ogn.commands.dbutils import session
from ogn.model import AddressOrigin, Device
from sqlalchemy import func, and_, true, false

from manager import Manager
manager = Manager()


def get_devices_stats(session):
    sq_nt = session.query(Device.address) \
        .filter(and_(Device.tracked == false(), Device.identified == true())) \
        .subquery()

    sq_ni = session.query(Device.address) \
        .filter(and_(Device.tracked == true(), Device.identified == false())) \
        .subquery()

    sq_ntni = session.query(Device.address) \
        .filter(and_(Device.tracked == false(), Device.identified == false())) \
        .subquery()

    query = session.query(Device.address_origin,
                          func.count(Device.id),
                          func.count(sq_nt.c.address),
                          func.count(sq_ni.c.address),
                          func.count(sq_ntni.c.address)) \
                   .outerjoin(sq_nt, sq_nt.c.address == Device.address) \
                   .outerjoin(sq_ni, sq_ni.c.address == Device.address) \
                   .outerjoin(sq_ntni, sq_ntni.c.address == Device.address) \
                   .group_by(Device.address_origin)

    stats = {}
    for [address_origin, device_count, nt_count, ni_count, ntni_count] in query.all():
        origin = AddressOrigin(address_origin).name()
        stats[origin] = {'device_count': device_count,
                         'nt_count': nt_count,
                         'ni_count': ni_count,
                         'ntni_count': ntni_count}
    return stats


@manager.command
def stats():
    """Show some stats on registered devices."""
    print('--- Devices ---')
    stats = get_devices_stats(session)
    for origin in stats:
        print('{:12s} Total:{:5d} - not tracked:{:3d}, not identified:{:3d}, not tracked & not identified: {:3d}'
              .format(origin,
                      stats[origin]['device_count'],
                      stats[origin]['nt_count'],
                      stats[origin]['ni_count'],
                      stats[origin]['ntni_count']))
