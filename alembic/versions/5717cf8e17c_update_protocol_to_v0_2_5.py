"""update protocol to v0.2.5

Revision ID: 5717cf8e17c
Revises: 4ebfb325db6
Create Date: 2016-10-17 19:16:38.632097

"""

# revision identifiers, used by Alembic.
revision = '5717cf8e17c'
down_revision = '4ebfb325db6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('aircraft_beacon', 'signal_strength', new_column_name='signal_quality')
    op.add_column('aircraft_beacon', sa.Column('signal_power', sa.Float))

    op.add_column('receiver_beacon', sa.Column('senders_visible', sa.Integer))
    op.add_column('receiver_beacon', sa.Column('senders_total', sa.Integer))
    op.add_column('receiver_beacon', sa.Column('senders_signal', sa.Float))
    op.add_column('receiver_beacon', sa.Column('senders_messages', sa.Integer))
    op.add_column('receiver_beacon', sa.Column('good_senders_signal', sa.Float))
    op.add_column('receiver_beacon', sa.Column('good_senders', sa.Integer))
    op.add_column('receiver_beacon', sa.Column('good_and_bad_senders', sa.Integer))

    op.add_column('receiver_beacon', sa.Column('voltage', sa.Float))
    op.add_column('receiver_beacon', sa.Column('amperage', sa.Float))


def downgrade():
    op.alter_column('aircraft_beacon', 'signal_quality', new_column_name='signal_strength')
    op.drop_column('aircraft_beacon', 'signal_power')

    op.drop_column('receiver_beacon', 'senders_visible')
    op.drop_column('receiver_beacon', 'senders_total')
    op.drop_column('receiver_beacon', 'senders_signal')
    op.drop_column('receiver_beacon', 'senders_messages')
    op.drop_column('receiver_beacon', 'good_senders_signal')
    op.drop_column('receiver_beacon', 'good_senders')
    op.drop_column('receiver_beacon', 'good_and_bad_senders')

    op.drop_column('receiver_beacon', 'voltage')
    op.drop_column('receiver_beacon', 'amperage')
