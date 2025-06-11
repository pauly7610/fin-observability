"""merge heads

Revision ID: b47a55659c8c
Revises: 20250610_add_incident_activity, 86ba5a3452cc
Create Date: 2025-06-10 16:30:25.353732

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b47a55659c8c"
down_revision: Union[str, None] = ("20250610_add_incident_activity", "86ba5a3452cc")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
