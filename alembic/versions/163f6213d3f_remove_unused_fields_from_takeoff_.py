"""remove unused fields from takeoff_landing

Revision ID: 163f6213d3f
Revises: 258a3f6bbdc
Create Date: 2016-06-03 20:05:20.749369

"""

# revision identifiers, used by Alembic.
revision = '163f6213d3f'
down_revision = '258a3f6bbdc'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('takeoff_landing', 'altitude')
    op.drop_column('takeoff_landing', 'ground_speed')


def downgrade():
    op.add_column('takeoff_landing', sa.Column('altitude', sa.Integer))
    op.add_column('takeoff_landing', sa.Column('ground_speed', sa.Float))
