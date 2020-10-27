from app import db
from app.utils import get_sql_trustworthy

SQL_TRUSTWORTHY = get_sql_trustworthy(source_table_alias='sp')

def create_views():
    db.session.execute(f"""
        DROP VIEW IF EXISTS receiver_ranking CASCADE;

        CREATE VIEW receiver_ranking AS
        SELECT
            r.name AS receiver_name,
            r.id AS receiver_id,
            MAX(rs.max_distance) AS max_distance,
            SUM(rs.max_normalized_quality * rs.messages_count) / SUM(rs.messages_count) AS max_normalized_quality,
            SUM(rs.messages_count) AS messages_count,
            COUNT(DISTINCT rs.sender_id) AS senders_count,
            COUNT(DISTINCT rs.location_mgrs_short) AS coverage_count
        FROM coverage_statistics AS rs
        INNER JOIN receivers AS r ON rs.receiver_id = r.id
        WHERE rs.date = NOW()::date AND rs.is_trustworthy IS TRUE AND rs.max_distance IS NOT NULL
        GROUP BY rs.date, r.name, r.id
        ORDER BY max_distance DESC;
    """)

    db.session.execute(f"""
        DROP VIEW IF EXISTS sender_ranking CASCADE;

        CREATE VIEW sender_ranking AS
        SELECT
            s.name,
            s.id AS sender_id,
            MAX(rs.max_distance) AS max_distance,
            SUM(rs.max_normalized_quality * rs.messages_count) / SUM(rs.messages_count) AS max_normalized_quality,
            SUM(rs.messages_count) AS messages_count,
            COUNT(DISTINCT rs.receiver_id) AS receivers_count,
            COUNT(DISTINCT rs.location_mgrs_short) AS coverage_count
        FROM coverage_statistics AS rs
        INNER JOIN senders AS s ON rs.sender_id = s.id
        WHERE rs.date = NOW()::date AND rs.is_trustworthy IS TRUE AND rs.max_distance IS NOT NULL
        GROUP BY rs.date, s.name, s.id
        ORDER BY max_distance DESC;
    """)

    db.session.commit()

def create_timescaledb_views():
    # 1. Since the reference_timestamps are strictly increasing we can set
    #    the parameter 'refresh_lag' to a very short time so the materialization
    #    starts right after the bucket is finished
    # 2. The feature realtime aggregation from TimescaleDB is quite time consuming.
    #    So we set materialized_only=true

    ### Sender statistics
    # These stats will be used in the daily ranking, so we make the bucket < 1d
    db.session.execute(f"""
        DROP VIEW IF EXISTS sender_stats_1h CASCADE;
        
        CREATE VIEW sender_stats_1h
        WITH (timescaledb.continuous, timescaledb.materialized_only=true, timescaledb.refresh_lag='5 minutes') AS
        SELECT
            time_bucket(INTERVAL '1 hour', sp.reference_timestamp) AS bucket,
            sp.name,
            ({SQL_TRUSTWORTHY}) AS is_trustworthy,
            COUNT(sp.*) AS beacon_count,
            MAX(sp.distance) AS max_distance,
            MIN(sp.altitude) AS min_altitude,
            MAX(sp.altitude) AS max_altitude

        FROM sender_positions AS sp
        GROUP BY bucket, sp.name, is_trustworthy;
    """)

    # ... and just for curiosity also bucket = 1d
    db.session.execute(f"""
        DROP VIEW IF EXISTS sender_stats_1d CASCADE;

        CREATE VIEW sender_stats_1d
        WITH (timescaledb.continuous, timescaledb.materialized_only=true, timescaledb.refresh_lag='1 hour') AS
        SELECT
            time_bucket(INTERVAL '1 day', sp.reference_timestamp) AS bucket,
            sp.name,
            ({SQL_TRUSTWORTHY}) AS is_trustworthy,
            COUNT(sp.*) AS beacon_count,
            MAX(sp.distance) AS max_distance,
            MIN(sp.altitude) AS min_altitude,
            MAX(sp.altitude) AS max_altitude

        FROM sender_positions AS sp
        GROUP BY bucket, sp.name, is_trustworthy;
    """)

    ### Receiver statistics
    # These stats will be used in the daily ranking, so we make the bucket < 1d
    db.session.execute(f"""
        DROP VIEW IF EXISTS receiver_stats_1h CASCADE;

        CREATE VIEW receiver_stats_1h
        WITH (timescaledb.continuous, timescaledb.materialized_only=true, timescaledb.refresh_lag='5 minutes') AS
        SELECT
            time_bucket(INTERVAL '1 hour', sp.reference_timestamp) AS bucket,
            sp.receiver_name,
            ({SQL_TRUSTWORTHY}) AS is_trustworthy,
            COUNT(sp.*) AS beacon_count,
            MAX(sp.distance) AS max_distance,
            MIN(sp.altitude) AS min_altitude,
            MAX(sp.altitude) AS max_altitude

        FROM sender_positions AS sp
        GROUP BY bucket, sp.receiver_name, is_trustworthy;
    """)

    # ... and just for curiosity also bucket = 1d
    db.session.execute(f"""
        DROP VIEW IF EXISTS receiver_stats_1d CASCADE;

        CREATE VIEW receiver_stats_1d
        WITH (timescaledb.continuous, timescaledb.materialized_only=true, timescaledb.refresh_lag='1 hour') AS
        SELECT
            time_bucket(INTERVAL '1 day', sp.reference_timestamp) AS bucket,
            sp.receiver_name,
            ({SQL_TRUSTWORTHY}) AS is_trustworthy,
            COUNT(sp.*) AS beacon_count,
            MAX(sp.distance) AS max_distance,
            MIN(sp.altitude) AS min_altitude,
            MAX(sp.altitude) AS max_altitude

        FROM sender_positions AS sp
        GROUP BY bucket, sp.receiver_name, is_trustworthy;
    """)
    
    ### Relation statistics (sender <-> receiver)
    # these stats will be used on a >= 1d basis, so we make the bucket = 1d
    db.session.execute(f"""
        DROP VIEW IF EXISTS relation_stats_1d CASCADE;

        CREATE VIEW relation_stats_1d
        WITH (timescaledb.continuous, timescaledb.materialized_only=true, timescaledb.refresh_lag='1 hour') AS
        SELECT
            time_bucket(INTERVAL '1 day', sp.reference_timestamp) AS bucket,
            sp.name,
            sp.receiver_name,
            ({SQL_TRUSTWORTHY}) AS is_trustworthy,
            COUNT(sp.*) AS beacon_count,
            MAX(sp.normalized_quality) AS max_normalized_quality,
            MAX(sp.distance) AS max_distance

        FROM sender_positions AS sp
        GROUP BY bucket, sp.name, sp.receiver_name, is_trustworthy;
    """)

    db.session.commit()


"""
class MyView(db.Model):
    __table__ = db.Table(
        'device_stats', db.metadata,
        db.Column('bucket', db.DateTime, primary_key=True),
        db.Column('name', db.String, primary_key=True),
        db.Column('beacon_count', db.Integer),
        autoload=True,
        autoload_with=db.engine
    )
"""