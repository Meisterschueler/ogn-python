from ogn.db import session
from ogn.model import Flarm
from ogn.ognutils import get_devices_from_ddb


def put_into_db(beacon):
    session.add(beacon)
    session.commit()


def fill_flarm_db():
    session.query(Flarm).delete()
    flarms = get_devices_from_ddb()
    session.bulk_save_objects(flarms)
    session.commit()

if __name__ == '__main__':
    fill_flarm_db()
