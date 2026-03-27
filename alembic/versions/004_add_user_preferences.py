"""add_user_preferences

Revision ID: 004
Revises: 003
Create Date: 2026-03-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_preferred_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "category_id", name="uq_user_preferred_category"),
    )
    op.create_index(op.f("ix_user_preferred_categories_id"), "user_preferred_categories", ["id"], unique=False)
    op.create_index(op.f("ix_user_preferred_categories_user_id"), "user_preferred_categories", ["user_id"], unique=False)

    op.execute("ALTER TABLE user_interactions DROP CONSTRAINT IF EXISTS unique_user_place_interaction")
    op.create_unique_constraint("unique_user_place_interaction", "user_interactions", ["user_id", "place_id"])

    op.add_column("places", sa.Column("reviews_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("places", "reviews_count")

    op.drop_constraint("unique_user_place_interaction", "user_interactions", type_="unique")

    op.drop_index(op.f("ix_user_preferred_categories_user_id"), table_name="user_preferred_categories")
    op.drop_index(op.f("ix_user_preferred_categories_id"), table_name="user_preferred_categories")
    op.drop_table("user_preferred_categories")
