"""TakeoffLanding: add status, remove duration

Revision ID: 0c66dabb0be9
Revises: 5717cf8e17c
Create Date: 2016-10-31 17:54:24.170607

"""

# revision identifiers, used by Alembic.
revision = '0c66dabb0be9'
down_revision = '5717cf8e17c'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('aircraft_beacon', sa.Column('status', sa.SmallInteger))
    op.create_index('ix_aircraft_beacon_status', 'aircraft_beacon', ['status'])
    op.drop_column('logbook', 'duration')


def downgrade():
    op.drop_column('aircraft_beacon', 'status')
    op.add_column('logbook', sa.Column('duration', sa.Interval))
