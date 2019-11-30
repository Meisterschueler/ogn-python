"""Remove non position fields from AircraftBeacon and ReceiverBeacon

Revision ID: 079fe885ae20
Revises: 6c19cedf5fa7
Create Date: 2019-09-25 21:42:34.924732

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '079fe885ae20'
down_revision = '6c19cedf5fa7'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('aircraft_beacons_receiver_id_fkey', 'aircraft_beacons', type_='foreignkey')
    op.drop_constraint('aircraft_beacons_device_id_fkey', 'aircraft_beacons', type_='foreignkey')
    op.drop_column('aircraft_beacons', 'device_id')
    op.drop_column('aircraft_beacons', 'receiver_id')

    op.drop_constraint('receiver_beacons_receiver_id_fkey', 'receiver_beacons', type_='foreignkey')
    op.drop_column('receiver_beacons', 'receiver_id')

    op.drop_column('receiver_beacons', 'total_ram')
    op.drop_column('receiver_beacons', 'senders_visible')
    op.drop_column('receiver_beacons', 'senders_messages')
    op.drop_column('receiver_beacons', 'cpu_temp')
    op.drop_column('receiver_beacons', 'platform')
    op.drop_column('receiver_beacons', 'rec_input_noise')
    op.drop_column('receiver_beacons', 'ntp_error')
    op.drop_column('receiver_beacons', 'good_senders')
    op.drop_column('receiver_beacons', 'senders_total')
    op.drop_column('receiver_beacons', 'cpu_load')
    op.drop_column('receiver_beacons', 'free_ram')
    op.drop_column('receiver_beacons', 'good_and_bad_senders')
    op.drop_column('receiver_beacons', 'amperage')
    op.drop_column('receiver_beacons', 'voltage')
    op.drop_column('receiver_beacons', 'senders_signal')
    op.drop_column('receiver_beacons', 'version')
    op.drop_column('receiver_beacons', 'relay')
    op.drop_column('receiver_beacons', 'rt_crystal_correction')
    op.drop_column('receiver_beacons', 'good_senders_signal')


def downgrade():
    op.add_column('receiver_beacons', sa.Column('receiver_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('receiver_beacons_receiver_id_fkey', 'receiver_beacons', 'receivers', ['receiver_id'], ['id'], ondelete='SET NULL')

    op.add_column('receiver_beacons', sa.Column('good_senders_signal', sa.REAL(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('rt_crystal_correction', sa.REAL(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('relay', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('version', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('senders_signal', sa.REAL(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('voltage', sa.REAL(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('amperage', sa.REAL(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('good_and_bad_senders', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('free_ram', sa.REAL(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('cpu_load', sa.REAL(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('senders_total', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('good_senders', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('ntp_error', sa.REAL(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('rec_input_noise', sa.REAL(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('platform', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('cpu_temp', sa.REAL(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('senders_messages', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('senders_visible', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('receiver_beacons', sa.Column('total_ram', sa.REAL(), autoincrement=False, nullable=True))

    op.add_column('aircraft_beacons', sa.Column('receiver_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('aircraft_beacons', sa.Column('device_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('aircraft_beacons_device_id_fkey', 'aircraft_beacons', 'devices', ['device_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('aircraft_beacons_receiver_id_fkey', 'aircraft_beacons', 'receivers', ['receiver_id'], ['id'], ondelete='SET NULL')
