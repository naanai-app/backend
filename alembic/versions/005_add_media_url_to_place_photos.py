"""refactor_place_photos_to_idx_only

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
    op.add_column("place_photos", sa.Column("idx", sa.Integer(), nullable=True))

    op.alter_column("place_photos", "idx", nullable=False)
    op.create_unique_constraint("uq_place_photos_place_id_idx", "place_photos", ["place_id", "idx"])

    op.drop_column("place_photos", "file_path")


def downgrade() -> None:
    op.add_column("place_photos", sa.Column("file_path", sa.String(), nullable=True))

    op.execute("UPDATE place_photos SET file_path = '' WHERE file_path IS NULL")

    op.drop_constraint("uq_place_photos_place_id_idx", "place_photos", type_="unique")
    op.drop_column("place_photos", "idx")
    op.alter_column("place_photos", "file_path", nullable=False)
