"""add audit_trail table with regulation_tags and parent_audit_id

Revision ID: 20250612_audit_trail
Revises: 20250612_sysconfig
Create Date: 2025-06-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20250612_audit_trail"
down_revision: Union[str, None] = "20250612_sysconfig"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "audit_trail" not in tables:
        op.create_table(
            "audit_trail",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("entity_type", sa.String(), nullable=False),
            sa.Column("entity_id", sa.String(), nullable=True),
            sa.Column("actor_type", sa.String(), nullable=False),
            sa.Column("actor_id", sa.Integer(), nullable=True),
            sa.Column("summary", sa.String(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=True),
            sa.Column("regulation_tags", sa.JSON(), nullable=True),
            sa.Column("parent_audit_id", sa.Integer(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["parent_audit_id"], ["audit_trail.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_audit_trail_id"), "audit_trail", ["id"], unique=False)
        op.create_index(op.f("ix_audit_trail_event_type"), "audit_trail", ["event_type"])
        op.create_index(op.f("ix_audit_trail_entity_type"), "audit_trail", ["entity_type"])
        op.create_index(op.f("ix_audit_trail_entity_id"), "audit_trail", ["entity_id"])
    else:
        cols = [c["name"] for c in inspector.get_columns("audit_trail")]
        if "regulation_tags" not in cols:
            op.add_column("audit_trail", sa.Column("regulation_tags", sa.JSON(), nullable=True))
        if "parent_audit_id" not in cols:
            op.add_column("audit_trail", sa.Column("parent_audit_id", sa.Integer(), nullable=True))
            op.create_foreign_key(
                "fk_audit_trail_parent",
                "audit_trail",
                "audit_trail",
                ["parent_audit_id"],
                ["id"],
            )


def downgrade() -> None:
    op.drop_table("audit_trail")
