from datetime import datetime
from tqdm import tqdm
from manager import Manager
from ogn.commands.dbutils import session
from ogn.commands.database import get_database_days

from ogn.collect.stats import create_device_stats, create_receiver_stats, create_relation_stats,\
    update_qualities, update_receivers as update_receivers_command, update_devices as update_devices_command,\
    update_device_stats_jumps

manager = Manager()


@manager.command
def create_stats(start=None, end=None):
    """Create DeviceStats, ReceiverStats and RelationStats."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, '%Y-%m-%d'))
        result = create_device_stats(session=session, date=single_date)
        result = update_device_stats_jumps(session=session, date=single_date)
        result = create_receiver_stats(session=session, date=single_date)
        result = create_relation_stats(session=session, date=single_date)
        result = update_qualities(session=session, date=single_date)


@manager.command
def update_receivers():
    """Update receivers with data from stats."""

    result = update_receivers_command(session=session)
    print(result)


@manager.command
def update_devices():
    """Update devices with data from stats."""

    result = update_devices_command(session=session)
    print(result)


@manager.command
def create_flights(start=None, end=None):
    """Create Flights."""

    days = get_database_days(start, end)

    pbar = tqdm(days)
    for single_date in pbar:
        pbar.set_description(datetime.strftime(single_date, '%Y-%m-%d'))
        result = _create_flights2d(session=session, date=single_date)


def _create_flights2d(session=None, date=None):
    SQL = """
        INSERT INTO flights2d
            (
                date,
                device_id,
                path
            )
        SELECT   sq5.date,
                 sq5.device_id,
                 st_collect(sq5.linestring ORDER BY sq5.part) multilinestring
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
                                    WHEN sq2.t1 - sq2.t2 < interval'100s'
                                    AND    st_distancesphere(sq2.l1, sq2.l2) < 1000 THEN 0
                                    ELSE 1
                             END AS ping
                      FROM   (
                          SELECT   sq.timestamp                                                                                 t1,
                                   lag(sq.timestamp) OVER (partition BY sq.timestamp::date, sq.device_id ORDER BY sq.timestamp) t2,
                                   sq.location                                                                                  l1,
                                   lag(sq.location) OVER (partition BY sq.timestamp::date, sq.device_id ORDER BY sq.timestamp)  l2,
                                   sq.device_id                                                                                 d1,
                                   lag(sq.device_id) OVER (partition BY sq.timestamp::date, sq.device_id ORDER BY sq.timestamp) d2
                          FROM     (
                                SELECT   timestamp,
                                         device_id,
                                         location,
                                         row_number() OVER (partition BY timestamp::date, device_id, timestamp ORDER BY error_count) message_number
                                FROM     aircraft_beacons
                                WHERE    timestamp::date = '{}' ) sq
                          WHERE    sq.message_number = 1 ) sq2 ) sq3 ) sq4
                          GROUP BY sq4.timestamp::date,
                                   sq4.device_id,
                                   sq4.part ) sq5
        GROUP BY sq5.date,
                 sq5.device_id
        ON CONFLICT DO NOTHING;
    """

    result = session.execute(SQL.format(date.strftime("%Y-%m-%d")))
    insert_counter = result.rowcount
    session.commit()
    return "Inserted {} Flights for {}".format(insert_counter, date.strftime("%Y-%m-%d"))
