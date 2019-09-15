"""Use Enums for DeviceInfoOrigin

Revision ID: be9a6dad551e
Revises: 885123e6a2d6
Create Date: 2019-09-15 14:38:25.838089

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql    


# revision identifiers, used by Alembic.
revision = 'be9a6dad551e'
down_revision = '885123e6a2d6'
branch_labels = None
depends_on = None

deviceinfoorigin = postgresql.ENUM('UNKNOWN', 'OGN_DDB', 'FLARMNET', 'USER_DEFINED', name='deviceinfoorigin')

def upgrade():
    deviceinfoorigin.create(op.get_bind())
    
    op.add_column('device_infos', sa.Column('address_origin_enum', sa.Enum('UNKNOWN', 'OGN_DDB', 'FLARMNET', 'USER_DEFINED', name='deviceinfoorigin'), nullable=False, server_default='UNKNOWN'))
    op.execute("UPDATE device_infos SET address_origin_enum = 'UNKNOWN' WHERE address_origin = 0")
    op.execute("UPDATE device_infos SET address_origin_enum = 'OGN_DDB' WHERE address_origin = 1")
    op.execute("UPDATE device_infos SET address_origin_enum = 'FLARMNET' WHERE address_origin = 2")
    op.execute("UPDATE device_infos SET address_origin_enum = 'USER_DEFINED' WHERE address_origin = 3")
    op.drop_column('device_infos', 'address_origin')
    op.alter_column('device_infos', 'address_origin_enum', new_column_name='address_origin')

def downgrade():
    op.add_column('device_infos', sa.Column('address_origin_int', sa.SmallInteger))
    op.execute("UPDATE device_infos SET address_origin_int = 0 WHERE address_origin = 'UNKNOWN'")
    op.execute("UPDATE device_infos SET address_origin_int = 1 WHERE address_origin = 'OGN_DDB'")
    op.execute("UPDATE device_infos SET address_origin_int = 2 WHERE address_origin = 'FLARMNET'")
    op.execute("UPDATE device_infos SET address_origin_int = 3 WHERE address_origin = 'USER_DEFINED'")
    op.drop_column('device_infos', 'address_origin')
    op.alter_column('device_infos', 'address_origin_int', new_column_name='address_origin')

    deviceinfoorigin.drop(op.get_bind())
