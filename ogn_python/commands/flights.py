from flask.cli import AppGroup
import click

from datetime import datetime
from tqdm import tqdm

from ogn_python.commands.database import get_database_days
from ogn_python import db

user_cli = AppGroup('flights')
user_cli.help = "Create 2D flight paths from data."

NOTHING = ''
CONTEST_RELEVANT = 'AND agl < 1000'
LOW_PASS = 'AND agl < 50 and ground_speed > 250'


def compute_gaps(session, date):
    query = """
        INSERT INTO flights2d(date, flight_type, device_id, path)
        SELECT  '{date}' AS date,
                3 AS flight_type,
                sq3.device_id,
                ST_Collect(sq3.path)
        FROM (
            SELECT  sq2.d1 device_id,
                    ST_MakeLine(sq2.l1, sq2.l2) path
            FROM
               (
                  SELECT sq.timestamp t1,
                     LAG(sq.timestamp) OVER ( PARTITION BY sq.timestamp::DATE, sq.device_id ORDER BY sq.timestamp) t2,
                     sq.location l1,
                     LAG(sq.location) OVER ( PARTITION BY sq.timestamp::DATE, sq.device_id ORDER BY sq.timestamp) l2,
                     sq.device_id d1,
                     LAG(sq.device_id) OVER ( PARTITION BY sq.timestamp::DATE, sq.device_id ORDER BY sq.timestamp) d2
                  FROM
                     (
                        SELECT DISTINCT ON (device_id, timestamp) timestamp, device_id, location, agl
                        FROM aircraft_beacons
                        WHERE    timestamp BETWEEN '{date} 00:00:00' AND '{date} 23:59:59' AND agl > 300
                        ORDER BY device_id, timestamp, error_count
                     ) sq
               ) sq2
            WHERE EXTRACT(epoch FROM sq2.t1 - sq2.t2) > 300
                AND ST_DistanceSphere(sq2.l1, sq2.l2) / EXTRACT(epoch FROM sq2.t1 - sq2.t2) BETWEEN 15 AND 50
            ) sq3
        GROUP BY sq3.device_id
        ON CONFLICT DO NOTHING;
    """.format(date=date.strftime('%Y-%m-%d'))

    session.execute(query)
    session.commit()


def compute_flights2d(session, date, flight_type):
    if flight_type == 0:
        filter = NOTHING
    elif flight_type == 1:
        filter = CONTEST_RELEVANT
    elif flight_type == 2:
        filter = LOW_PASS

    query = """
    INSERT INTO flights2d
    (
    date,
    flight_type,
    device_id,
    path,
    path_simple
    )
    SELECT  '{date}' AS date,
            {flight_type} as flight_type,
            sq5.device_id,
            st_collect(sq5.linestring order BY sq5.part) multilinestring,
            st_collect(st_simplify(sq5.linestring, 0.0001) ORDER BY sq5.part) simple_multilinestring
    FROM     (
        SELECT  sq4.device_id,
                sq4.part,
                st_makeline(sq4.location ORDER BY sq4.timestamp) linestring
        FROM     (
            SELECT  sq3.timestamp,
                    sq3.location,
                    sq3.device_id,
                    sum(sq3.ping) OVER (partition BY sq3.device_id ORDER BY sq3.timestamp) part
            FROM     (
                SELECT sq2.t1 AS timestamp,
                    sq2.l1 AS location,
                    sq2.d1    device_id,
                    CASE
                        WHEN sq2.t1 - sq2.t2 < interval'100s' AND ST_DistanceSphere(sq2.l1, sq2.l2) < 1000 THEN 0
                        ELSE 1
                    END AS ping
                FROM   (
                    SELECT  sq.timestamp                                                             t1,
                            lag(sq.timestamp) OVER (partition BY sq.device_id ORDER BY sq.timestamp) t2,
                            sq.location                                                              l1,
                            lag(sq.location) OVER (partition BY sq.device_id ORDER BY sq.timestamp)  l2,
                            sq.device_id                                                             d1,
                            lag(sq.device_id) OVER (partition BY sq.device_id ORDER BY sq.timestamp) d2
                    FROM     (
                        SELECT   DISTINCT ON (device_id, timestamp) timestamp, device_id, location
                        FROM     aircraft_beacons
                        WHERE    timestamp BETWEEN '{date} 00:00:00' AND '{date} 23:59:59' {filter}
                        ORDER BY device_id, timestamp, error_count
                    ) sq
                ) sq2
            ) sq3
        ) sq4
        GROUP BY sq4.device_id, sq4.part
    ) sq5
    GROUP BY sq5.device_id
    ON CONFLICT DO NOTHING;
    """.format(date=date.strftime('%Y-%m-%d'),
               flight_type=flight_type,
               filter=filter)
    session.execute(query)
    session.commit()


@user_cli.command('create')
@click.argument('start')
@click.argument('end')
@click.argument('flight_type', type=click.INT)
def create(start, end, flight_type):
    """Compute flights. Flight type: 0: all flights, 1: below 1000m AGL, 2: below 50m AGL + faster than 250 km/h, 3: inverse coverage'"""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, '%Y-%m-%d'))
        if flight_type <= 2:
            result = compute_flights2d(session=db.session, date=single_date, flight_type=flight_type)
        else:
            result = compute_gaps(session=db.session, date=single_date)
