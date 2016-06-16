"""Create relations

Revision ID: 46d818bc09b
Revises: 2004ce1566c
Create Date: 2016-05-18 21:00:24.832298

"""

# revision identifiers, used by Alembic.
revision = '46d818bc09b'
down_revision = '2004ce1566c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import geoalchemy2 as ga


def upgrade():
    op.add_column('aircraft_beacon', sa.Column('device_id', sa.Integer))
    op.create_foreign_key("aircraft_beacon_device_id_fkey", "aircraft_beacon", "device", ["device_id"], ["id"], ondelete="SET NULL")
    op.create_index('ix_aircraft_beacon_device_id', 'aircraft_beacon', ['device_id'])

    op.add_column('aircraft_beacon', sa.Column('receiver_id', sa.Integer))
    op.create_foreign_key("aircraft_beacon_receiver_id_fkey", "aircraft_beacon", "receiver", ["receiver_id"], ["id"], ondelete="SET NULL")
    op.create_index('ix_aircraft_beacon_receiver_id', 'aircraft_beacon', ['receiver_id'])

    op.drop_index('ix_aircraft_beacon_address', 'aircraft_beacon')

    op.add_column('receiver_beacon', sa.Column('receiver_id', sa.Integer))
    op.create_foreign_key("receiver_beacon_receiver_id_fkey", "receiver_beacon", "receiver", ["receiver_id"], ["id"], ondelete="SET NULL")
    op.create_index('ix_receiver_beacon_receiver_id', 'receiver_beacon', ['receiver_id'])


    op.add_column('takeoff_landing', sa.Column('airport_id', sa.Integer))
    op.create_foreign_key("takeoff_landing_airport_id_fkey", "takeoff_landing", "airport", ["airport_id"], ["id"], ondelete="SET NULL")
    op.create_index('ix_takeoff_landing_airport_id', 'takeoff_landing', ['airport_id'])

    op.add_column('takeoff_landing', sa.Column('device_id', sa.Integer))
    op.create_foreign_key('takeoff_landing_device_id_fkey', 'takeoff_landing', 'device', ['device_id'], ['id'], ondelete="SET NULL")
    op.create_index('ix_takeoff_landing_device_id', 'takeoff_landing', ['device_id'])

    op.drop_index('ix_takeoff_landing_address', 'takeoff_landing')
    op.drop_index('idx_takeoff_landing_location', 'takeoff_landing')
    op.drop_column('takeoff_landing', 'address')
    op.drop_column('takeoff_landing', 'name')
    op.drop_column('takeoff_landing', 'receiver_name')
    op.drop_column('takeoff_landing', 'location')


def downgrade():
    op.drop_index('ix_aircraft_beacon_device_id', 'aircraft_beacon')
    op.drop_foreign_key("aircraft_beacon_device_id_fkey", "aircraft_beacon")
    op.drop_column('aircraft_beacon', 'device_id')

    op.drop_index('ix_aircraft_beacon_receiver_id', 'aircraft_beacon')
    op.drop_foreign_key("aircraft_beacon_receiver_id_fkey", "aircraft_beacon")
    op.drop_column('aircraft_beacon', 'receiver_id')

    op.create_index('ix_aircraft_beacon_address', sa.Column('address', sa.String))


    op.drop_index('ix_receiver_beacon_receiver_id', 'receiver_beacon')
    op.drop_foreign_key("ix_receiver_beacon_receiver_id", "receiver_beacon")
    op.drop_column('receiver_beacon', 'receiver_id')


    op.drop_index('ix_takeoff_landing_airport_id', 'takeoff_landing')
    op.drop_foreign_key("takeoff_landing_airport_id_fkey", "takeoff_landing")
    op.drop_column('takeoff_landing', 'airport_id')

    op.drop_index('ix_takeoff_landing_device_id', 'takeoff_landing')
    op.drop_foreign_key("takeoff_landing_device_id_fkey", "takeoff_landing")
    op.drop_column('takeoff_landing', 'device_id')

    op.add_column('takeoff_landing', sa.Column('name', sa.String))
    op.add_column('takeoff_landing', sa.Column('receiver_name', sa.String(9)))
    op.add_column('takeoff_landing', sa.Column('address', sa.String(6)))
    op.add_column('takeoff_landing', sa.Column('location', ga.Geometry('POINT', srid=4326)))
    op.create_index('ix_takeoff_landing_address', 'takeoff_landing', ['address'])
    op.create_index('idx_takeoff_landing_location', 'takeoff_landing', ['location'])

