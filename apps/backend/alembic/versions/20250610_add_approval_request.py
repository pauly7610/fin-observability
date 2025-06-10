"""
Revision ID: 20250610_add_approval_request
Revises: 
Create Date: 2025-06-10 13:04:30
"""
from alembic import op
import sqlalchemy as sa
import enum

# revision identifiers, used by Alembic.
revision = '20250610_add_approval_request'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'approval_requests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('resource_type', sa.String(), index=True),
        sa.Column('resource_id', sa.String(), index=True),
        sa.Column('requested_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'escalated', name='approvalstatus'), default='pending'),
        sa.Column('reason', sa.String()),
        sa.Column('decision_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('decision_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
    )

def downgrade():
    op.drop_table('approval_requests')
    op.execute("DROP TYPE IF EXISTS approvalstatus")
