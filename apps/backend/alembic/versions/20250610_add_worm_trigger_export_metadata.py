"""
Alembic migration for WORM (Write Once, Read Many) enforcement on export_metadata table.
Blocks DELETEs and only allows UPDATEs to delivery_status, verification_status, delivered_at, and verified_at.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250610_worm_export_metadata'
down_revision = '89dde0c4a8db'
branch_labels = None
depends_on = None

def upgrade():
    op.execute('''
    CREATE OR REPLACE FUNCTION enforce_worm_export_metadata()
    RETURNS trigger AS $$
    BEGIN
        -- Block DELETEs
        IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'WORM policy: export_metadata rows cannot be deleted';
        END IF;
        -- Block UPDATEs except for allowed fields
        IF TG_OP = 'UPDATE' THEN
            IF NEW.delivery_status IS DISTINCT FROM OLD.delivery_status
               OR NEW.verification_status IS DISTINCT FROM OLD.verification_status
               OR NEW.delivered_at IS DISTINCT FROM OLD.delivered_at
               OR NEW.verified_at IS DISTINCT FROM OLD.verified_at THEN
                IF (NEW.export_type IS DISTINCT FROM OLD.export_type)
                   OR (NEW.file_path IS DISTINCT FROM OLD.file_path)
                   OR (NEW.hash IS DISTINCT FROM OLD.hash)
                   OR (NEW.signature IS DISTINCT FROM OLD.signature)
                   OR (NEW.requested_by IS DISTINCT FROM OLD.requested_by)
                   OR (NEW.delivered_to IS DISTINCT FROM OLD.delivered_to)
                   OR (NEW.delivery_method IS DISTINCT FROM OLD.delivery_method)
                   OR (NEW.created_at IS DISTINCT FROM OLD.created_at)
                   OR (NEW.meta IS DISTINCT FROM OLD.meta) THEN
                    RAISE EXCEPTION 'WORM policy: Only status/verification fields can be updated in export_metadata';
                END IF;
            ELSE
                RAISE EXCEPTION 'WORM policy: Only status/verification fields can be updated in export_metadata';
            END IF;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    DROP TRIGGER IF EXISTS export_metadata_worm_enforcer ON export_metadata;
    CREATE TRIGGER export_metadata_worm_enforcer
        BEFORE UPDATE OR DELETE ON export_metadata
        FOR EACH ROW
        EXECUTE FUNCTION enforce_worm_export_metadata();
    ''')

def downgrade():
    op.execute('''
    DROP TRIGGER IF EXISTS export_metadata_worm_enforcer ON export_metadata;
    DROP FUNCTION IF EXISTS enforce_worm_export_metadata();
    ''')
