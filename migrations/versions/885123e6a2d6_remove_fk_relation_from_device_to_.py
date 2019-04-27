"""Remove FK relation from device to device_info

Revision ID: 885123e6a2d6
Revises: 002656878233
Create Date: 2019-04-27 14:22:30.841969

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '885123e6a2d6'
down_revision = '002656878233'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('ix_device_infos_device_id', table_name='device_infos')
    op.drop_constraint('device_infos_device_id_fkey', 'device_infos', type_='foreignkey')
    op.drop_column('device_infos', 'device_id')


def downgrade():
    op.add_column('device_infos', sa.Column('device_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('device_infos_device_id_fkey', 'device_infos', 'devices', ['device_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_device_infos_device_id', 'device_infos', ['device_id'], unique=False)
