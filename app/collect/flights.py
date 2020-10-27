from datetime import date

from app import db

NOTHING = ""
CONTEST_RELEVANT = "AND agl < 1000"
LOW_PASS = "AND agl < 50 and ground_speed > 250"

def compute_flights(date, flight_type=0):
    if flight_type == 0:
        filter = NOTHING
    elif flight_type == 1:
        filter = CONTEST_RELEVANT
    elif flight_type == 2:
        filter = LOW_PASS

    date_str = date.strftime("%Y-%m-%d")

    query = f"""
        INSERT INTO flights(date, sender_id, flight_type, multilinestring, simple_multilinestring)
        SELECT  '{date_str}' AS date,
                s.id AS sender_id,
                {flight_type} as flight_type,
                st_collect(sq5.linestring order BY sq5.part) multilinestring,
                st_collect(st_simplify(sq5.linestring, 0.0001) ORDER BY sq5.part) simple_multilinestring
        FROM     (
            SELECT  sq4.name,
                    sq4.part,
                    st_makeline(sq4.location ORDER BY sq4.timestamp) AS linestring
            FROM     (
                SELECT  sq3.timestamp,
                        sq3.location,
                        sq3.name,
                        SUM(sq3.ping) OVER (partition BY sq3.name ORDER BY sq3.timestamp) AS part
                FROM     (
                    SELECT  sq2.t1 AS timestamp,
                            sq2.l1 AS location,
                            sq2.s1 AS name,
                            CASE
                                WHEN sq2.s1 = sq2.s2 AND sq2.t1 - sq2.t2 < interval'100s' AND ST_DistanceSphere(sq2.l1, sq2.l2) < 1000 THEN 0
                                ELSE 1
                            END AS ping
                    FROM   (
                        SELECT  sq.timestamp                                                        t1,
                                lag(sq.timestamp) OVER (partition BY sq.name ORDER BY sq.timestamp) t2,
                                sq.location                                                         l1,
                                lag(sq.location) OVER (partition BY sq.name ORDER BY sq.timestamp)  l2,
                                sq.name                                                             s1,
                                lag(sq.name) OVER (partition BY sq.name ORDER BY sq.timestamp)      s2
                        FROM     (
                            SELECT   DISTINCT ON (name, timestamp) name, timestamp, location
                            FROM     sender_positions
                            WHERE    reference_timestamp BETWEEN '{date_str} 00:00:00' AND '{date_str} 23:59:59' {filter}
                            ORDER BY name, timestamp, error_count
                        ) AS sq
                    ) AS sq2
                ) AS sq3
            ) AS sq4
            GROUP BY sq4.name, sq4.part
        ) AS sq5
        INNER JOIN senders AS s ON sq5.name = s.name
        GROUP BY s.id
        ON CONFLICT DO NOTHING;
    """

    db.session.execute(query)
    db.session.commit()

def compute_gaps(date):
    date_str = date.strftime("%Y-%m-%d")

    query = f"""
        INSERT INTO flights(date, flight_type, sender_id, multilinestring)
        SELECT  '{date_str}' AS date,
                3 AS flight_type,
                s.id AS sender_id,
                ST_Collect(sq3.path)
        FROM (
            SELECT  sq2.s1 AS name,
                    ST_MakeLine(sq2.l1, sq2.l2) AS path
            FROM
                (
                SELECT  sq.timestamp t1,
                        LAG(sq.timestamp) OVER (PARTITION BY sq.timestamp::DATE, sq.name ORDER BY sq.timestamp) t2,
                        sq.location l1,
                        LAG(sq.location) OVER (PARTITION BY sq.timestamp::DATE, sq.name ORDER BY sq.timestamp) l2,
                        sq.name s1,
                        LAG(sq.name) OVER (PARTITION BY sq.timestamp::DATE, sq.name ORDER BY sq.timestamp) s2
                FROM
                (
                    SELECT DISTINCT ON (name, timestamp) name, timestamp, location, agl
                    FROM sender_positions
                    WHERE    reference_timestamp BETWEEN '{date_str} 00:00:00' AND '{date_str} 23:59:59' AND agl > 300
                    ORDER BY name, timestamp, error_count
                ) AS sq
            ) AS sq2
            WHERE EXTRACT(epoch FROM sq2.t1 - sq2.t2) > 300
            AND ST_DistanceSphere(sq2.l1, sq2.l2) / EXTRACT(epoch FROM sq2.t1 - sq2.t2) BETWEEN 15 AND 50
        ) AS sq3
        INNER JOIN senders AS s on sq3.name = s.name
        GROUP BY s.id
        ON CONFLICT DO NOTHING;
    """

    db.session.execute(query)
    db.session.commit()

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        result = compute_flights(date=date(2020, 10, 28))
        print(result)