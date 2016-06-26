"""Added DeviceInfo

Revision ID: 4ebfb325db6
Revises: 163f6213d3f
Create Date: 2016-06-04 11:11:00.546524

"""

# revision identifiers, used by Alembic.
revision = '4ebfb325db6'
down_revision = '163f6213d3f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute("CREATE TABLE device_info AS SELECT * FROM device;")
    op.create_index('ix_device_info_address', 'device_info', ['address'])
    op.drop_column('device_info', 'name')
    op.drop_column('device_info', 'airport')
    op.drop_column('device_info', 'frequency')

    op.drop_column('device', 'address_origin')
    op.drop_column('device', 'name')
    op.drop_column('device', 'airport')
    op.drop_column('device', 'aircraft')
    op.drop_column('device', 'registration')
    op.drop_column('device', 'competition')
    op.drop_column('device', 'frequency')
    op.drop_column('device', 'tracked')
    op.drop_column('device', 'identified')

    op.add_column('device', sa.Column('stealth', sa.Boolean))
    op.add_column('device', sa.Column('software_version', sa.Float))
    op.add_column('device', sa.Column('hardware_version', sa.SmallInteger))
    op.add_column('device', sa.Column('real_address', sa.String(6)))


def downgrade():
    op.add_column('device', sa.Column('address_origin', sa.SmallInteger))
    op.add_column('device', sa.Column('name', sa.Unicode))
    op.add_column('device', sa.Column('airport', sa.String))
    op.add_column('device', sa.Column('aircraft', sa.String))
    op.add_column('device', sa.Column('registration', sa.String(7)))
    op.add_column('device', sa.Column('competition', sa.String(3)))
    op.add_column('device', sa.Column('frequency', sa.String))
    op.add_column('device', sa.Column('tracked', sa.Boolean))
    op.add_column('device', sa.Column('identified', sa.Boolean))

    op.create_index('ix_device_info_registration', 'device', ['registration'])

    op.drop_column('device', 'stealth')
    op.drop_column('device', 'software_version')
    op.drop_column('device', 'hardware_version')
    op.drop_column('device', 'real_address')

    # transfer from device_info to device costs too much...
    op.execute("DROP TABLE device_info;")
    pass
