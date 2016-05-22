"""correct airport scheme

Revision ID: 7585491482
Revises: 46d818bc09b
Create Date: 2016-05-21 20:19:24.865915

"""

# revision identifiers, used by Alembic.
revision = '7585491482'
down_revision = '46d818bc09b'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute('ALTER TABLE airport ALTER COLUMN code TYPE varchar(6)')


def downgrade():
    op.execute('ALTER TABLE airport ALTER COLUMN code TYPE varchar(5)')
