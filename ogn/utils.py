import requests
import csv
from io import StringIO
from math import sin, cos, asin, atan2, sqrt, pi

from .model import Device, AddressOrigin

from geopy.geocoders import Nominatim

DDB_URL = "http://ddb.glidernet.org/download"

deg2rad = pi/180
rad2deg = 1/deg2rad

address_prefixes = {'F':'FLR',
                    'O':'OGN',
                    'I':'ICA'}


def get_ddb(csvfile=None):
    if csvfile is None:
        r = requests.get(DDB_URL)
        rows = '\n'.join(i for i in r.text.splitlines() if i[0] != '#')
        address_origin = AddressOrigin.ogn_ddb
    else:
        r = open(csvfile, 'r')
        rows = ''.join(i for i in r.readlines() if i[0] != '#')
        address_origin = AddressOrigin.user_defined

    data = csv.reader(StringIO(rows), quotechar="'", quoting=csv.QUOTE_ALL)

    devices = list()
    for row in data:
        flarm = Device()
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


def get_trackable(ddb):
   l = []
   for i in ddb:
       if i.tracked and i.address_type in address_prefixes:
           l.append('{}{}'.format(address_prefixes[i.address_type], i.address))
   return l


def get_country_code(latitude, longitude):
    geolocator = Nominatim()
    location = geolocator.reverse("%f, %f" % (latitude, longitude))
    try:
        country_code = location.raw["address"]["country_code"]
    except KeyError:
        country_code = None
    return country_code


def wgs84_to_sphere(lat1, lat2, lon1, lon2, alt1, alt2):
    lat1 = lat1*deg2rad
    lat2 = lat2*deg2rad
    lon1 = lon1*deg2rad
    lon2 = lon2*deg2rad
    radius = 6366000*2*asin(sqrt((sin((lat1-lat2)/2))**2 + cos(lat1)*cos(lat2)*(sin((lon1-lon2)/2))**2))
    theta = atan2(alt2-alt1, radius)*rad2deg
    phi = atan2(sin(lon2-lon1)*cos(lat2), cos(lat1)*sin(lat2)-sin(lat1)*cos(lat2)*cos(lon2-lon1))*rad2deg
    return radius, theta, phi
