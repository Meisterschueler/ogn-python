"""Migrate to PostGIS

Revision ID: 277aca1b810
Revises: 3a0765c9a2
Create Date: 2016-04-23 08:01:49.059187

"""

# revision identifiers, used by Alembic.
revision = '277aca1b810'
down_revision = '3a0765c9a2'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import geoalchemy2 as ga

UPGRADE_QUERY = """
UPDATE {table_name}
SET
    location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);
"""

DOWNGRADE_QUERY = """
UPDATE {table_name}
SET
    latitude = ST_Y(ST_TRANSFORM(location, 4326)),
    longitude = ST_X(ST_TRANSFORM(location, 4326));
"""

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;");
    op.add_column('airport', sa.Column('location', ga.Geometry('POINT', srid=4326)))
    op.execute(UPGRADE_QUERY.format(table_name='airport'))
    op.drop_column('airport', 'latitude')
    op.drop_column('airport', 'longitude')

    op.add_column('aircraft_beacon', sa.Column('location', ga.Geometry('POINT', srid=4326)))
    op.execute(UPGRADE_QUERY.format(table_name='aircraft_beacon'))
    op.drop_column('aircraft_beacon', 'latitude')
    op.drop_column('aircraft_beacon', 'longitude')

    op.add_column('receiver_beacon', sa.Column('location', ga.Geometry('POINT', srid=4326)))
    op.execute(UPGRADE_QUERY.format(table_name='receiver_beacon'))
    op.drop_column('receiver_beacon', 'latitude')
    op.drop_column('receiver_beacon', 'longitude')

    op.add_column('receiver', sa.Column('location', ga.Geometry('POINT', srid=4326)))
    op.execute(UPGRADE_QUERY.format(table_name='receiver'))
    op.drop_column('receiver', 'latitude')
    op.drop_column('receiver', 'longitude')

    op.add_column('takeoff_landing', sa.Column('location', ga.Geometry('POINT', srid=4326)))
    op.execute(UPGRADE_QUERY.format(table_name='takeoff_landing'))
    op.drop_column('takeoff_landing', 'latitude')
    op.drop_column('takeoff_landing', 'longitude')


def downgrade():
    op.add_column('airport', sa.Column('latitude', sa.FLOAT))
    op.add_column('airport', sa.Column('longitude', sa.FLOAT))
    op.execute(DOWNGRADE_QUERY.format(table_name='airport'))
    op.drop_column('airport', 'location')

    op.add_column('aircraft_beacon', sa.Column('latitude', sa.FLOAT))
    op.add_column('aircraft_beacon', sa.Column('longitude', sa.FLOAT))
    op.execute(DOWNGRADE_QUERY.format(table_name='aircraft_beacon'))
    op.drop_column('aircraft_beacon', 'location')

    op.add_column('receiver_beacon', sa.Column('latitude', sa.FLOAT))
    op.add_column('receiver_beacon', sa.Column('longitude', sa.FLOAT))
    op.execute(DOWNGRADE_QUERY.format(table_name='receiver_beacon'))
    op.drop_column('receiver_beacon', 'location')

    op.add_column('receiver', sa.Column('latitude', sa.FLOAT))
    op.add_column('receiver', sa.Column('longitude', sa.FLOAT))
    op.execute(DOWNGRADE_QUERY.format(table_name='receiver'))
    op.drop_column('receiver', 'location')

    op.add_column('takeoff_landing', sa.Column('latitude', sa.FLOAT))
    op.add_column('takeoff_landing', sa.Column('longitude', sa.FLOAT))
    op.execute(DOWNGRADE_QUERY.format(table_name='takeoff_landing'))
    op.drop_column('takeoff_landing', 'location')

    op.execute("DROP EXTENSION postgis;");
