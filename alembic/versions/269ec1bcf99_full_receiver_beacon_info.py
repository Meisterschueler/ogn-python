"""Full receiver beacon info

Revision ID: 269ec1bcf99
Revises: 2c7144443d8
Create Date: 2016-01-19 22:22:50.275615

"""

# revision identifiers, used by Alembic.
revision = '269ec1bcf99'
down_revision = '2c7144443d8'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('receiver_beacon', sa.Column('cpu_load', sa.Float))
    op.add_column('receiver_beacon', sa.Column('cpu_temp', sa.Float))
    op.add_column('receiver_beacon', sa.Column('free_ram', sa.Float))
    op.add_column('receiver_beacon', sa.Column('total_ram', sa.Float))
    op.add_column('receiver_beacon', sa.Column('ntp_error', sa.Float))
    op.add_column('receiver_beacon', sa.Column('rt_crystal_correction', sa.Float))
    op.add_column('receiver_beacon', sa.Column('rec_input_noise', sa.Float))


def downgrade():
    op.drop_column('receiver_beacon', 'cpu_load')
    op.drop_column('receiver_beacon', 'cpu_temp')
    op.drop_column('receiver_beacon', 'free_ram')
    op.drop_column('receiver_beacon', 'total_ram')
    op.drop_column('receiver_beacon', 'ntp_error')
    op.drop_column('receiver_beacon', 'rt_crystal_correction')
    op.drop_column('receiver_beacon', 'rec_input_noise')

