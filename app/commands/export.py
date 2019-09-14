from flask.cli import AppGroup
import click

import datetime
import re
import csv

from aerofiles.igc import Writer
from app.model import AircraftBeacon, Device
from app import db

user_cli = AppGroup("export")
user_cli.help = "Export data in several file formats."


@user_cli.command("cup")
def cup():
    """Export receiver waypoints as '.cup'."""

    sql = """
        SELECT
            'OGN-' || sq.name AS name,
            sq.name AS code,
            c.iso2 AS country,
            CASE WHEN sq.lat_deg < 10 THEN '0' ELSE '' END || CAST((sq.lat_deg*100 + sq.lat_min) AS decimal(18, 5)) || sq.lat_sig AS lat,
            CASE WHEN sq.lon_deg < 10 THEN '00' WHEN sq.lon_deg < 100 THEN '0' ELSE '' END || CAST(sq.lon_deg*100 + sq.lon_min AS decimal(18, 5)) || sq.lon_sig AS lon,
            altitude || 'm' AS elev,
            '8' AS style,
            '' AS rwdir,
            '' AS rwlen,
            '' AS freq,
            'lastseen: ' || sq.lastseen::date || ', version: ' || sq.version || ', platform: ' || sq.platform AS desc
        FROM (
            SELECT
                st_y(location) as lat,
                CASE WHEN ST_Y(location) > 0 THEN 'N' ELSE 'S' END AS lat_sig,
                FLOOR(ABS(ST_Y(location))) AS lat_deg,
                60*(ABS(ST_Y(location)) - FLOOR(ABS(ST_Y(location)))) AS lat_min,
                st_x(location) AS lon,
                CASE WHEN ST_X(location) > 0 THEN 'E' ELSE 'W' END AS lon_sig,
                FLOOR(ABS(ST_X(location))) AS lon_deg,
                60*(ABS(ST_X(location)) - FLOOR(ABS(ST_X(location)))) AS lon_min
                , *
            FROM receivers
            WHERE lastseen - firstseen > INTERVAL'3 MONTH' AND lastseen > '2018-01-01 00:00:00' AND name NOT LIKE 'FNB%'
            ) sq
        INNER JOIN countries c ON c.gid = sq.country_id
        ORDER BY sq.name;
        """
    results = db.session.execute(sql)

    with open("receivers.cup", "w") as outfile:
        outcsv = csv.writer(outfile)
        outcsv.writerow(results.keys())
        outcsv.writerows(results.fetchall())


@user_cli.command("igc")
@click.argument("address")
@click.argument("date")
def igc(address, date):
    """Export igc file for <address> at <date>."""
    if not re.match(".{6}", address):
        print("Address {} not valid.".format(address))
        return

    if not re.match(r"\d{4}-\d{2}-\d{2}", date):
        print("Date {} not valid.".format(date))
        return

    device_id = db.session.query(Device.id).filter(Device.address == address).first()

    if device_id is None:
        print("Device with address '{}' not found.".format(address))
        return

    with open("sample.igc", "wb") as fp:
        writer = Writer(fp)

        writer.write_headers(
            {
                "manufacturer_code": "OGN",
                "logger_id": "OGN",
                "date": datetime.date(1987, 2, 24),
                "fix_accuracy": 50,
                "pilot": "Konstantin Gruendger",
                "copilot": "",
                "glider_type": "Duo Discus",
                "glider_id": "D-KKHH",
                "firmware_version": "2.2",
                "hardware_version": "2",
                "logger_type": "LXNAVIGATION,LX8000F",
                "gps_receiver": "uBLOX LEA-4S-2,16,max9000m",
                "pressure_sensor": "INTERSEMA,MS5534A,max10000m",
                "competition_id": "2H",
                "competition_class": "Doubleseater",
            }
        )

        points = (
            db.session.query(AircraftBeacon)
            .filter(AircraftBeacon.device_id == device_id)
            .filter(AircraftBeacon.timestamp > date + " 00:00:00")
            .filter(AircraftBeacon.timestamp < date + " 23:59:59")
            .order_by(AircraftBeacon.timestamp)
        )

        for point in points.all():
            writer.write_fix(point.timestamp.time(), latitude=point.location.latitude, longitude=point.location.longitude, valid=True, pressure_alt=point.altitude, gps_alt=point.altitude)
