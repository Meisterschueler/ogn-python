from urllib.request import urlopen

from .db import session
from .model import AddressOrigin, Flarm


def get_devices_from_ddb():
    session.query(Flarm.address_origin == AddressOrigin.ogn_ddb).delete()

    response = urlopen("http://ddb.glidernet.org/download")
    lines = response.readlines()
    for line in lines:
        if (line.decode()[0] == "#"):
            continue

        flarm = Flarm()
        flarm.parse_ogn(line.decode())
        session.add(flarm)

    session.commit()


def get_devices_from_flarmnet():
    session.query(Flarm.address_origin == AddressOrigin.flarmnet).delete()

    response = urlopen("http://flarmnet.org/files/data.fln")
    lines = response.readlines()
    for line in lines:
        if (len(line) != Flarm.FLARMNET_LINE_LENGTH):
            continue

        flarm = Flarm()
        flarm.parse_flarmnet(line.decode())
        session.add(flarm)

    session.commit()


def put_position_into_db(position):
    session.add(position)
    session.commit()


def put_receiver_into_db(receiver):
    session.add(receiver)
    session.commit()


if __name__ == '__main__':
    get_devices_from_ddb()
    get_devices_from_flarmnet()
