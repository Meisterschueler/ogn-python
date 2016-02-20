"""hardware version hex to dec

Revision ID: 3a0765c9a2
Revises: 269ec1bcf99
Create Date: 2016-02-20 10:31:55.520815

"""

# revision identifiers, used by Alembic.
revision = '3a0765c9a2'
down_revision = '269ec1bcf99'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()
    res = conn.execute("UPDATE aircraft_beacon "
                       "SET hardware_version = "
                       "16 * (hardware_version / 10) + (hardware_version % 10) "
                       "WHERE hardware_version IS NOT NULL")


def downgrade():
    conn = op.get_bind()
    res = conn.execute("UPDATE aircraft_beacon "
                       "SET hardware_version = "
                       "10 * (hardware_version / 16) + (hardware_version % 16) "
                       "WHERE hardware_version IS NOT NULL")
