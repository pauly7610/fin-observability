"""merge indexes and b47a55659c8c

Revision ID: c606d74171a7
Revises: 20250610_add_indexes, b47a55659c8c
Create Date: 2025-06-10 17:20:41.670184

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c606d74171a7"
down_revision: Union[str, None] = ("20250610_add_indexes", "b47a55659c8c")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
