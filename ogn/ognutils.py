import requests
import csv
from io import StringIO

from .model import Flarm, AddressOrigin

from geopy.geocoders import Nominatim

DDB_URL = "http://ddb.glidernet.org/download"


def get_ddb(csvfile=None):
    if csvfile is None:
        r = requests.get(DDB_URL)
        rows = '\n'.join(i for i in r.text.splitlines() if i[0] != '#')
        address_origin = AddressOrigin.ogn_ddb
    else:
        r = open(csvfile, 'r')
        rows = ''.join(i for i in r.readlines() if i[0] != '#')
        address_origin = AddressOrigin.userdefined

    data = csv.reader(StringIO(rows), quotechar="'", quoting=csv.QUOTE_ALL)

    devices = list()
    for row in data:
        flarm = Flarm()
        flarm.address_type = row[0]
        flarm.address = row[1]
        flarm.aircraft = row[2]
        flarm.registration = row[3]
        flarm.competition = row[4]
        flarm.tracked = row[5] == 'Y'
        flarm.identified = row[6] == 'Y'

        flarm.address_origin = address_origin

        devices.append(flarm)

    return devices


def get_country_code(latitude, longitude):
    geolocator = Nominatim()
    location = geolocator.reverse("%f, %f" % (latitude, longitude))
    country_code = location.raw["address"]["country_code"]
    return country_code
