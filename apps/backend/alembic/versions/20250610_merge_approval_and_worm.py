"""
Revision ID: 20250610_merge_approval_and_worm
Revises: 20250610_add_approval_request, 20250610_worm_export_metadata
Create Date: 2025-06-10 13:18:30
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250610_merge_approval_and_worm'
down_revision = ('20250610_add_approval_request', '20250610_worm_export_metadata')
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
