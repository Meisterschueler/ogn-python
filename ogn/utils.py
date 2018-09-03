import csv
import gzip
from io import StringIO

from aerofiles.seeyou import Reader
from geopy.exc import GeopyError
from geopy.geocoders import Nominatim
from ogn.parser.utils import FEETS_TO_METER
import requests

from .model import DeviceInfoOrigin, DeviceInfo, Airport, Location


DDB_URL = "http://ddb.glidernet.org/download/?t=1"


address_prefixes = {'F': 'FLR',
                    'O': 'OGN',
                    'I': 'ICA'}

nm2m = 1852
mi2m = 1609.34


def get_ddb(csvfile=None, address_origin=DeviceInfoOrigin.unknown):
    if csvfile is None:
        r = requests.get(DDB_URL)
        rows = '\n'.join(i for i in r.text.splitlines() if i[0] != '#')
    else:
        r = open(csvfile, 'r')
        rows = ''.join(i for i in r.readlines() if i[0] != '#')

    data = csv.reader(StringIO(rows), quotechar="'", quoting=csv.QUOTE_ALL)

    device_infos = list()
    for row in data:
        device_info = DeviceInfo()
        device_info.address_type = row[0]
        device_info.address = row[1]
        device_info.aircraft = row[2]
        device_info.registration = row[3]
        device_info.competition = row[4]
        device_info.tracked = row[5] == 'Y'
        device_info.identified = row[6] == 'Y'
        device_info.aircraft_type = int(row[7])
        device_info.address_origin = address_origin

        device_infos.append(device_info)

    return device_infos


def get_trackable(ddb):
    l = []
    for i in ddb:
        if i.tracked and i.address_type in address_prefixes:
            l.append("{}{}".format(address_prefixes[i.address_type], i.address))
    return l


def get_country_code(latitude, longitude):
    geolocator = Nominatim()
    try:
        location = geolocator.reverse("{}, {}".format(latitude, longitude))
        country_code = location.raw['address']['country_code']
    except KeyError:
        country_code = None
    except GeopyError:
        country_code = None
    return country_code


def get_airports(cupfile):
    airports = list()
    with open(cupfile) as f:
        for line in f:
            try:
                for waypoint in Reader([line]):
                    if waypoint['style'] > 5:   # reject unlandable places
                        continue

                    airport = Airport()
                    airport.name = waypoint['name']
                    airport.code = waypoint['code']
                    airport.country_code = waypoint['country']
                    airport.style = waypoint['style']
                    airport.description = waypoint['description']
                    location = Location(waypoint['longitude'], waypoint['latitude'])
                    airport.location_wkt = location.to_wkt()
                    airport.altitude = waypoint['elevation']['value']
                    if (waypoint['elevation']['unit'] == 'ft'):
                        airport.altitude = airport.altitude * FEETS_TO_METER
                    airport.runway_direction = waypoint['runway_direction']
                    airport.runway_length = waypoint['runway_length']['value']
                    if (waypoint['runway_length']['unit'] == 'nm'):
                        airport.altitude = airport.altitude * nm2m
                    elif (waypoint['runway_length']['unit'] == 'ml'):
                        airport.altitude = airport.altitude * mi2m
                    airport.frequency = waypoint['frequency']

                    airports.append(airport)
            except AttributeError as e:
                print('Failed to parse line: {} {}'.format(line, e))

    return airports


def open_file(filename):
    """Opens a regular or unzipped textfile for reading."""
    f = open(filename, 'rb')
    a = f.read(2)
    f.close()
    if (a == b'\x1f\x8b'):
        f = gzip.open(filename, 'rt')
        return f
    else:
        f = open(filename, 'rt')
        return f
    
from math import radians, cos, sin, asin, sqrt, atan2, degrees

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371000.785 # Radius of earth in meters
    d = c * r
    
    # calculate bearing
    bearing = atan2(sin(dlon)*cos(lat2), cos(lat1)*sin(lat2)-sin(lat1)*cos(lat2)*cos(dlon))
    bearing = (degrees(bearing) + 360) % 360
    
    return d,bearing