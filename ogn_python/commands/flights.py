from flask.cli import AppGroup
import click

from datetime import datetime
from tqdm import tqdm

from ogn_python.commands.database import get_database_days
from ogn_python import db

user_cli = AppGroup('flights')
user_cli.help = "Create 2D flight paths from data."


def compute_flights2d(session, date):
    query = """
    INSERT INTO flights2d
    (
    date,
    device_id,
    path,
    path_simple
    )
    SELECT   sq5.date,
    sq5.device_id,
    st_collect(sq5.linestring order BY sq5.part) multilinestring,
    st_collect(st_simplify(sq5.linestring ORDER BY sq5.part) simple_multilinestring
    FROM     (
        SELECT   sq4.timestamp::date AS date,
        sq4.device_id,
        sq4.part,
        st_makeline(sq4.location ORDER BY sq4.timestamp) linestring
        FROM     (
            SELECT   sq3.timestamp,
            sq3.location,
            sq3.device_id,
            sum(sq3.ping) OVER (partition BY sq3.timestamp::date, sq3.device_id ORDER BY sq3.timestamp) part
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
                        WHERE    timestamp BETWEEN '{0} 00:00:00' AND '{0} 23:59:59'
                        ORDER BY device_id, timestamp, error_count
                    ) sq
                ) sq2
            ) sq3
        ) sq4
        GROUP BY sq4.timestamp::date, sq4.device_id, sq4.part
    ) sq5
    GROUP BY sq5.date, sq5.device_id
    ON CONFLICT DO NOTHING;
    """.format(date.strftime('%Y-%m-%d'))
    session.execute(query)
    session.commit()


@user_cli.command('create')
@click.argument('start')
@click.argument('end')
def create(start, end):
    """Compute flights."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, '%Y-%m-%d'))
        result = compute_flights2d(session=db.session, date=single_date)
