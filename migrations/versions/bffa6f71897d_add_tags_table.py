"""add tags table

Revision ID: bffa6f71897d
Revises: cd82f290f33e
Create Date: 2025-03-20 21:40:23.168620

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "bffa6f71897d"
down_revision: Union[str, None] = "cd82f290f33e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "tags",
        sa.Column("uid", sa.UUID(), nullable=False),
        sa.Column("name", sa.VARCHAR(), nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("uid"),
    )
    op.create_table(
        "booktag",
        sa.Column("book_id", sa.Uuid(), nullable=False),
        sa.Column("tag_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["book_id"],
            ["books.uid"],
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.uid"],
        ),
        sa.PrimaryKeyConstraint("book_id", "tag_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("booktag")
    op.drop_table("tags")
    # ### end Alembic commands ###
