"""
Alembic migration for incident activity/audit trail
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250610_add_incident_activity"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "incident_activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "incident_id",
            sa.String(),
            sa.ForeignKey("incidents.incident_id"),
            index=True,
        ),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("old_value", sa.String(), nullable=True),
        sa.Column("new_value", sa.String(), nullable=True),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("meta", postgresql.JSON(), nullable=True),
        sa.Column(
            "timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade():
    op.drop_table("incident_activities")
