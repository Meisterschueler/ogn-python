"""logbook changes

Revision ID: 2c7144443d8
Revises: 104107d119d
Create Date: 2015-11-27 22:05:31.417449

"""

# revision identifiers, used by Alembic.
revision = '2c7144443d8'
down_revision = '104107d119d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('aircraft_beacon', 'real_id', new_column_name='real_address')
    op.add_column('aircraft_beacon', sa.Column('flight_state', sa.SmallInteger))
    op.create_index('ix_aircraft_beacon_flight_state', 'aircraft_beacon', ['flight_state'])


def downgrade():
    op.alter_column('aircraft_beacon', 'real_address', new_column_name='real_id')
    op.drop_column('aircraft_beacon', 'flight_state')
    op.drop_index('ix_aircraft_beacon_flight_state', 'aircraft_beacon')
