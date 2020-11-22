from flask import current_app

from mgrs import MGRS

from ogn.parser import parse

from app.model import AircraftType

#import rasterio as rs
#elevation_dataset = rs.open('/Volumes/LaCieBlack/Wtf4.tiff')

mgrs = MGRS()


def aprs_string_to_message(aprs_string):
    try:
        message = parse(aprs_string, calculate_relations=True)
    except Exception as e:
        current_app.logger.debug(e)
        return None

    if message['aprs_type'] not in ('position', 'status'):
        return None

    elif message['aprs_type'] == 'position':
        latitude = message["latitude"]
        longitude = message["longitude"]

        message["location"] = "SRID=4326;POINT({} {})".format(longitude, latitude)

        location_mgrs = mgrs.toMGRS(latitude, longitude).decode("utf-8")
        message["location_mgrs"] = location_mgrs
        message["location_mgrs_short"] = location_mgrs[0:5] + location_mgrs[5:7] + location_mgrs[10:12]

        #if 'altitude' in message and longitude >= 0.0 and longitude <= 20.0 and latitude >= 40.0 and latitude <= 60.0:
        #    elevation = [val[0] for val in elevation_dataset.sample(((longitude, latitude),))][0]
        #    message['agl'] = message['altitude'] - elevation

        if 'bearing' in message:
            bearing = int(message['bearing'])
            message['bearing'] = bearing if bearing < 360 else 0

        if "aircraft_type" in message:
            message["aircraft_type"] = AircraftType(message["aircraft_type"]) if message["aircraft_type"] in AircraftType.list() else AircraftType.UNKNOWN

        if "gps_quality" in message:
            if message["gps_quality"] is not None and "horizontal" in message["gps_quality"]:
                message["gps_quality_horizontal"] = message["gps_quality"]["horizontal"]
                message["gps_quality_vertical"] = message["gps_quality"]["vertical"]
            del message["gps_quality"]

    return message
