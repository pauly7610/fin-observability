"""
Archive or delete audit trail entries older than the retention period.

Per SEC 17a-4, compliance-relevant events are retained for 7 years. This script
removes entries older than AUDIT_RETENTION_YEARS (default 7).

Usage:
    python scripts/archive_audit_trail.py              # delete entries older than retention
    python scripts/archive_audit_trail.py --dry-run    # report count only, no deletion
    python scripts/archive_audit_trail.py --years 10   # override retention years

Run via cron for periodic archival, e.g.:
    0 2 * * 0  cd /app && python scripts/archive_audit_trail.py  # weekly, 2am Sunday
"""

import argparse
import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load .env from project root or apps/backend
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(_root, ".env"), os.path.join(_root, "apps", "backend", ".env")):
    if os.path.exists(p):
        load_dotenv(dotenv_path=p)
        break


def main():
    parser = argparse.ArgumentParser(description="Archive audit trail entries older than retention period")
    parser.add_argument("--dry-run", action="store_true", help="Report count only, do not delete")
    parser.add_argument("--years", type=int, default=None, help="Override AUDIT_RETENTION_YEARS")
    args = parser.parse_args()

    retention_years = args.years or int(os.getenv("AUDIT_RETENTION_YEARS", "7"))
    cutoff = datetime.utcnow() - timedelta(days=retention_years * 365)

    from apps.backend.database import SessionLocal
    from apps.backend.models import AuditTrailEntry

    db = SessionLocal()
    try:
        count = db.query(AuditTrailEntry).filter(AuditTrailEntry.timestamp < cutoff).count()
        print(f"Entries older than {retention_years} years (before {cutoff.isoformat()}): {count}")

        if count == 0:
            return 0

        if args.dry_run:
            print("Dry run: no changes made")
            return 0

        deleted = db.query(AuditTrailEntry).filter(AuditTrailEntry.timestamp < cutoff).delete()
        db.commit()
        print(f"Deleted {deleted} audit trail entries")
        return 0
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
