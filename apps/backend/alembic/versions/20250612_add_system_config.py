"""add system_config for generated keys

Revision ID: 20250612_sysconfig
Revises: c606d74171a7
Create Date: 2025-06-12

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20250612_sysconfig"
down_revision: Union[str, None] = "c606d74171a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "system_config",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("system_config")
