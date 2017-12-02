from manager import Manager
from ogn.commands.dbutils import session
from ogn.model import DeviceInfoOrigin
from ogn.model.device_info import DeviceInfo
from sqlalchemy import func, and_, true, false


manager = Manager()


def get_devices_stats(session):
    sq_default = session.query(DeviceInfo.address) \
        .filter(and_(DeviceInfo.tracked == true(), DeviceInfo.identified == true())) \
        .subquery()

    sq_nt = session.query(DeviceInfo.address) \
        .filter(and_(DeviceInfo.tracked == false(), DeviceInfo.identified == true())) \
        .subquery()

    sq_ni = session.query(DeviceInfo.address) \
        .filter(and_(DeviceInfo.tracked == true(), DeviceInfo.identified == false())) \
        .subquery()

    sq_ntni = session.query(DeviceInfo.address) \
        .filter(and_(DeviceInfo.tracked == false(), DeviceInfo.identified == false())) \
        .subquery()

    query = session.query(DeviceInfo.address_origin,
                          func.count(DeviceInfo.id),
                          func.count(sq_default.c.address),
                          func.count(sq_nt.c.address),
                          func.count(sq_ni.c.address),
                          func.count(sq_ntni.c.address)) \
                   .outerjoin(sq_default, sq_default.c.address == DeviceInfo.address) \
                   .outerjoin(sq_nt, sq_nt.c.address == DeviceInfo.address) \
                   .outerjoin(sq_ni, sq_ni.c.address == DeviceInfo.address) \
                   .outerjoin(sq_ntni, sq_ntni.c.address == DeviceInfo.address) \
                   .group_by(DeviceInfo.address_origin)

    stats = {}
    for [address_origin, device_count, default_count, nt_count, ni_count, ntni_count] in query.all():
        origin = DeviceInfoOrigin(address_origin).name()
        stats[origin] = {'device_count': device_count,
                         'default_count': default_count,
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
        print('{:12s} Total:{:5d} - default:{:3d}, just not tracked:{:3d}, just not identified:{:3d}, not tracked & not identified: {:3d}'
              .format(origin,
                      stats[origin]['device_count'],
                      stats[origin]['default_count'],
                      stats[origin]['nt_count'],
                      stats[origin]['ni_count'],
                      stats[origin]['ntni_count']))
