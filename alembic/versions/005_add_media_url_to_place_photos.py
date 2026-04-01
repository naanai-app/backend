"""add_media_url_to_place_photos

Revision ID: 005
Revises: 004
Create Date: 2026-04-01 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("place_photos", sa.Column("media_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("place_photos", "media_url")
