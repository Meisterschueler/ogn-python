from app import db


def drop_views():
    db.session.execute("DROP VIEW IF EXISTS device_stats CASCADE;")


def create_views():
    db.session.execute("""
        CREATE OR REPLACE VIEW device_stats
        WITH (timescaledb.continuous) AS
        SELECT
            time_bucket(INTERVAL '1 day', ab.timestamp) AS bucket,
            ab.name,
            COUNT(ab.name) AS beacon_count
        FROM aircraft_beacons AS ab
        GROUP BY bucket, ab.name;
    """)
    db.session.commit()


class MyView(db.Model):
    if not db.engine.has_table(db.engine, 'device_stats'):
        create_views()

    __table__ = db.Table(
        'device_stats', db.metadata,
        db.Column('bucket', db.DateTime, primary_key=True),
        db.Column('name', db.String, primary_key=True),
        db.Column('beacon_count', db.Integer),
        autoload=True,
        autoload_with=db.engine
    )
