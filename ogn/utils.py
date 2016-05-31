import requests
import csv
from io import StringIO

from .model import Device, Airport, Location

from geopy.geocoders import Nominatim
from geopy.exc import GeopyError

from aerofiles.seeyou import Reader
from ogn.parser.utils import feet2m

DDB_URL = "http://ddb.glidernet.org/download/?t=1"


address_prefixes = {'F': 'FLR',
                    'O': 'OGN',
                    'I': 'ICA'}

nm2m = 1852
mi2m = 1609.34


def get_ddb(csvfile=None):
    if csvfile is None:
        r = requests.get(DDB_URL)
        rows = '\n'.join(i for i in r.text.splitlines() if i[0] != '#')
    else:
        r = open(csvfile, 'r')
        rows = ''.join(i for i in r.readlines() if i[0] != '#')

    data = csv.reader(StringIO(rows), quotechar="'", quoting=csv.QUOTE_ALL)

    devices = list()
    for row in data:
        device = Device()
        device.address_type = row[0]
        device.address = row[1]
        device.aircraft = row[2]
        device.registration = row[3]
        device.competition = row[4]
        device.tracked = row[5] == 'Y'
        device.identified = row[6] == 'Y'
        device.aircraft_type = row[7]

        devices.append(device)

    return devices


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
                        airport.altitude = airport.altitude * feet2m
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
