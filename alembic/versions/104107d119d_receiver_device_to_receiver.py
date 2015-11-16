"""receiver_device to receiver

Revision ID: 104107d119d
Revises: 46bc73c49e0
Create Date: 2015-11-16 20:07:19.569378

"""

# revision identifiers, used by Alembic.
revision = '104107d119d'
down_revision = '46bc73c49e0'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.rename_table('receiver_device', 'receiver')


def downgrade():
    op.rename_table('receiver', 'receiver_device')
