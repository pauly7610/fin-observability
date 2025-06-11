"""
Alembic migration: add indexes to incident_activities for incident_id and timestamp
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250610_add_indexes"
down_revision = "20250610_add_approval_request"
branch_labels = None
depends_on = None


def upgrade():
    # Only create indexes if they do not already exist
    conn = op.get_bind()
    # incident_id index
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_indexes WHERE tablename = 'incident_activities' AND indexname = 'ix_incident_activities_incident_id'"
        )
    )
    if not result.fetchone():
        op.create_index(
            "ix_incident_activities_incident_id", "incident_activities", ["incident_id"]
        )
    # timestamp index
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_indexes WHERE tablename = 'incident_activities' AND indexname = 'ix_incident_activities_timestamp'"
        )
    )
    if not result.fetchone():
        op.create_index(
            "ix_incident_activities_timestamp", "incident_activities", ["timestamp"]
        )


def downgrade():
    op.drop_index(
        "ix_incident_activities_incident_id", table_name="incident_activities"
    )
    op.drop_index("ix_incident_activities_timestamp", table_name="incident_activities")
