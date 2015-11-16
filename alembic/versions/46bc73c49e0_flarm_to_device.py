"""flarm to device

Revision ID: 46bc73c49e0
Revises: 
Create Date: 2015-11-16 19:44:37.934741

"""

# revision identifiers, used by Alembic.
revision = '46bc73c49e0'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.rename_table('flarm', 'device')


def downgrade():
    op.rename_table('device', 'flarm')
