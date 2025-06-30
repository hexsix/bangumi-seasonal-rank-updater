"""init

Revision ID: 17b4121da2e2
Revises:
Create Date: 2025-06-30 22:59:40.983646

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "17b4121da2e2"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "index",
        sa.Column("season_id", sa.Integer, primary_key=True),
        sa.Column("index_id", sa.Integer, primary_key=True),
        sa.Column("subject_ids", sa.String, nullable=True),
    )
    op.create_table(
        "subject",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=True),
        sa.Column("name_cn", sa.String, nullable=True),
        sa.Column("images_grid", sa.String, nullable=True),
        sa.Column("images_large", sa.String, nullable=True),
        sa.Column("rank", sa.Integer, nullable=True),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("collection_total", sa.Integer, nullable=True),
        sa.Column("average_comment", sa.Float, nullable=True),
        sa.Column("drop_rate", sa.Float, nullable=True),
        sa.Column("air_weekday", sa.String, nullable=True),
        sa.Column("meta_tags", sa.String, nullable=True),
        sa.Column("updated_at", sa.String, nullable=False),
    )
    op.create_table(
        "yucwiki",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("jp_title", sa.String, nullable=False),
        sa.Column("subject_id", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("index")
    op.drop_table("subject")
    op.drop_table("yucwiki")
