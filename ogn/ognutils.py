from urllib.request import urlopen

from ogn.model import Flarm

from geopy.geocoders import Nominatim


def get_devices_from_ddb():
    devices = list()

    response = urlopen("http://ddb.glidernet.org/download")
    lines = response.readlines()
    for line in lines:
        if (line.decode()[0] == "#"):
            continue

        flarm = Flarm()
        flarm.parse_ogn(line.decode())
        devices.append(flarm)

    return devices


def get_country_code(latitude, longitude):
    geolocator = Nominatim()
    location = geolocator.reverse("%f, %f" % (latitude, longitude))
    country_code = location.raw["address"]["country_code"]
    return country_code
