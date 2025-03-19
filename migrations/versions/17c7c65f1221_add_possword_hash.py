"""add possword hash

Revision ID: 17c7c65f1221
Revises: ce8e59ac8b50
Create Date: 2025-03-14 23:51:15.210273

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "17c7c65f1221"
down_revision: Union[str, None] = "ce8e59ac8b50"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "users",
        sa.Column("password_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "password_hash")
    # ### end Alembic commands ###
