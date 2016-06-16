"""add aircraft_type to device

Revision ID: 258a3f6bbdc
Revises: 7585491482
Create Date: 2016-05-25 20:16:57.990249

"""

# revision identifiers, used by Alembic.
revision = '258a3f6bbdc'
down_revision = '7585491482'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('device', sa.Column('aircraft_type', sa.Integer))
    op.create_index('ix_device_aircraft_type', 'device', ['aircraft_type'])
    op.create_index('ix_aircraft_beacon_aircraft_type', 'aircraft_beacon', ['aircraft_type'])


def downgrade():
    op.drop_index('ix_aircraft_beacon_aircraft_type', 'aircraft_beacon')
    op.drop_index('ix_device_aircraft_type', 'device')
    op.drop_column('device', 'aircraft_type')
