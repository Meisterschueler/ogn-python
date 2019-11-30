"""Use Enum for AircraftType

Revision ID: 6c19cedf5fa7
Revises: be9a6dad551e
Create Date: 2019-09-24 18:37:40.224279

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6c19cedf5fa7'
down_revision = 'be9a6dad551e'
branch_labels = None
depends_on = None


aircrafttype = postgresql.ENUM('UNKNOWN', 'GLIDER_OR_MOTOR_GLIDER', 'TOW_TUG_PLANE', 'HELICOPTER_ROTORCRAFT',
                               'PARACHUTE', 'DROP_PLANE', 'HANG_GLIDER', 'PARA_GLIDER', 'POWERED_AIRCRAFT',
                               'JET_AIRCRAFT', 'FLYING_SAUCER', 'BALLOON', 'AIRSHIP', 'UNMANNED_AERIAL_VEHICLE',
                               'STATIC_OBJECT', name='aircrafttype')

def upgrade():
    aircrafttype.create(op.get_bind())

    for table in ['aircraft_beacons', 'devices']:
        op.add_column(table, sa.Column('aircraft_type_enum', sa.Enum(
            'UNKNOWN', 'GLIDER_OR_MOTOR_GLIDER', 'TOW_TUG_PLANE', 'HELICOPTER_ROTORCRAFT',
            'PARACHUTE', 'DROP_PLANE', 'HANG_GLIDER', 'PARA_GLIDER', 'POWERED_AIRCRAFT',
            'JET_AIRCRAFT', 'FLYING_SAUCER', 'BALLOON', 'AIRSHIP', 'UNMANNED_AERIAL_VEHICLE',
            'STATIC_OBJECT', name='aircrafttype'), nullable=False, server_default='UNKNOWN'))
        op.execute("""
            UPDATE {table} SET aircraft_type_enum = 'UNKNOWN' WHERE aircraft_type = 0;
            UPDATE {table} SET aircraft_type_enum = 'GLIDER_OR_MOTOR_GLIDER' WHERE aircraft_type = 1;
            UPDATE {table} SET aircraft_type_enum = 'TOW_TUG_PLANE' WHERE aircraft_type = 2;
            UPDATE {table} SET aircraft_type_enum = 'HELICOPTER_ROTORCRAFT' WHERE aircraft_type = 3;
            UPDATE {table} SET aircraft_type_enum = 'PARACHUTE' WHERE aircraft_type = 4;
            UPDATE {table} SET aircraft_type_enum = 'DROP_PLANE' WHERE aircraft_type = 5;
            UPDATE {table} SET aircraft_type_enum = 'HANG_GLIDER' WHERE aircraft_type = 6;
            UPDATE {table} SET aircraft_type_enum = 'PARA_GLIDER' WHERE aircraft_type = 7;
            UPDATE {table} SET aircraft_type_enum = 'POWERED_AIRCRAFT' WHERE aircraft_type = 8;
            UPDATE {table} SET aircraft_type_enum = 'JET_AIRCRAFT' WHERE aircraft_type = 9;
            UPDATE {table} SET aircraft_type_enum = 'FLYING_SAUCER' WHERE aircraft_type = 10;
            UPDATE {table} SET aircraft_type_enum = 'BALLOON' WHERE aircraft_type = 11;
            UPDATE {table} SET aircraft_type_enum = 'AIRSHIP' WHERE aircraft_type = 12;
            UPDATE {table} SET aircraft_type_enum = 'UNMANNED_AERIAL_VEHICLE' WHERE aircraft_type = 13;
            UPDATE {table} SET aircraft_type_enum = 'STATIC_OBJECT' WHERE aircraft_type = 15;
        """.format(table=table))
        op.drop_column(table, 'aircraft_type')
        op.alter_column(table, 'aircraft_type_enum', new_column_name='aircraft_type')

def downgrade():
    for table in ['aircraft_beacons', 'devices']:
        op.add_column(table, sa.Column('aircraft_type_int', sa.SmallInteger))
        op.execute("""
            UPDATE {table} SET aircraft_type_int = 0 WHERE aircraft_type = 'UNKNOWN';
            UPDATE {table} SET aircraft_type_int = 1 WHERE aircraft_type = 'GLIDER_OR_MOTOR_GLIDER';
            UPDATE {table} SET aircraft_type_int = 2 WHERE aircraft_type = 'TOW_TUG_PLANE';
            UPDATE {table} SET aircraft_type_int = 3 WHERE aircraft_type = 'HELICOPTER_ROTORCRAFT';
            UPDATE {table} SET aircraft_type_int = 4 WHERE aircraft_type = 'PARACHUTE';
            UPDATE {table} SET aircraft_type_int = 5 WHERE aircraft_type = 'DROP_PLANE';
            UPDATE {table} SET aircraft_type_int = 6 WHERE aircraft_type = 'HANG_GLIDER';
            UPDATE {table} SET aircraft_type_int = 7 WHERE aircraft_type = 'PARA_GLIDER';
            UPDATE {table} SET aircraft_type_int = 8 WHERE aircraft_type = 'POWERED_AIRCRAFT';
            UPDATE {table} SET aircraft_type_int = 9 WHERE aircraft_type = 'JET_AIRCRAFT';
            UPDATE {table} SET aircraft_type_int = 10 WHERE aircraft_type = 'FLYING_SAUCER';
            UPDATE {table} SET aircraft_type_int = 11 WHERE aircraft_type = 'BALLOON';
            UPDATE {table} SET aircraft_type_int = 12 WHERE aircraft_type = 'AIRSHIP';
            UPDATE {table} SET aircraft_type_int = 13 WHERE aircraft_type = 'UNMANNED_AERIAL_VEHICLE';
            UPDATE {table} SET aircraft_type_int = 15 WHERE aircraft_type = 'STATIC_OBJECT';
        """.format(table=table))
        op.drop_column(table, 'aircraft_type')
        op.alter_column(table, 'aircraft_type_int', new_column_name='aircraft_type')

    aircrafttype.drop(op.get_bind())