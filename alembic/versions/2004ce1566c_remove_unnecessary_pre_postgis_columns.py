"""remove unnecessary pre postgis columns

Revision ID: 2004ce1566c
Revises: 277aca1b810
Create Date: 2016-04-28 18:24:14.912833

"""

# revision identifiers, used by Alembic.
revision = '2004ce1566c'
down_revision = '277aca1b810'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import geoalchemy2 as ga


def upgrade():
    # POSTGIS is fast enough, so lets forget radius, theta and phi
    op.drop_column('aircraft_beacon', 'radius')
    op.drop_column('aircraft_beacon', 'theta')
    op.drop_column('aircraft_beacon', 'phi')

    # ... and flight_state is not used
    op.drop_column('aircraft_beacon', 'flight_state')


def downgrade():
    op.add_column('aircraft_beacon', sa.Column('radius', sa.Float))
    op.add_column('aircraft_beacon', sa.Column('theta', sa.Float))
    op.add_column('aircraft_beacon', sa.Column('phi', sa.Float))
    op.add_column('aircraft_beacon', sa.Column('flight_state', sa.SmallInteger))
