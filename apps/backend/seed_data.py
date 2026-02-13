"""
Seed script for PostgreSQL database.
Populates transactions, compliance logs, incidents, users, and system metrics.

Usage:
    python -m apps.backend.seed_data
    
Set DATABASE_URL env var to target Railway Postgres, or it defaults to local.
"""

import os
import sys
import random
import uuid
from datetime import datetime, timedelta

from apps.backend.database import SessionLocal, engine
from apps.backend.routers.auth import pwd_context
from apps.backend.models import (
    Base,
    User,
    Transaction,
    ComplianceLog,
    SystemMetric,
    Incident,
    AgentAction,
)

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# --- Config ---
NUM_TRANSACTIONS = int(os.environ.get("SEED_TRANSACTIONS", 10000))
NUM_COMPLIANCE_LOGS = int(os.environ.get("SEED_COMPLIANCE_LOGS", 500))
NUM_SYSTEM_METRICS = int(os.environ.get("SEED_SYSTEM_METRICS", 1000))
NUM_INCIDENTS = int(os.environ.get("SEED_INCIDENTS", 50))

CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"]
STATUSES = ["completed", "completed", "completed", "pending", "failed"]
SEVERITIES = ["low", "low", "medium", "medium", "high", "critical"]
INCIDENT_TYPES = ["stuck_order", "missed_trade", "spike", "latency", "compliance_breach"]
INCIDENT_STATUSES = ["open", "investigating", "resolved", "closed"]
DESKS = ["Equities", "Fixed Income", "FX", "Commodities", "Derivatives"]
TRADERS = ["alice", "bob", "charlie", "diana", "eve", "frank", "grace"]
METRIC_NAMES = [
    "api_latency_ms", "cpu_usage_percent", "memory_usage_percent",
    "db_query_time_ms", "request_rate_per_sec", "error_rate_percent",
    "queue_depth", "cache_hit_ratio",
]

random.seed(42)


def random_timestamp(days_back=30):
    """Generate a random timestamp within the last N days."""
    now = datetime.utcnow()
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return now - delta


def generate_amount():
    """Generate realistic transaction amounts with some anomalies."""
    if random.random() < 0.05:  # 5% anomalies — large amounts
        return round(random.uniform(50000, 500000), 2)
    if random.random() < 0.1:  # 10% small transactions
        return round(random.uniform(1, 100), 2)
    return round(random.uniform(100, 25000), 2)


def seed_users(db):
    """Create seed users if they don't exist."""
    users = [
        {"email": "admin@finobs.io", "full_name": "Admin User", "role": "admin"},
        {"email": "analyst@finobs.io", "full_name": "Jane Analyst", "role": "analyst"},
        {"email": "compliance@finobs.io", "full_name": "Bob Compliance", "role": "compliance"},
        {"email": "viewer@finobs.io", "full_name": "View Only", "role": "viewer"},
    ]
    created = 0
    for u in users:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            db.add(User(
                email=u["email"],
                hashed_password=pwd_context.hash("seed_password"),
                full_name=u["full_name"],
                role=u["role"],
                is_active=True,
            ))
            created += 1
    db.commit()
    print(f"  Users: {created} created, {len(users) - created} already existed")
    return db.query(User).all()


def seed_transactions(db):
    """Seed transactions with realistic financial data."""
    existing = db.query(Transaction).count()
    if existing >= NUM_TRANSACTIONS:
        print(f"  Transactions: {existing} already exist, skipping")
        return

    to_create = NUM_TRANSACTIONS - existing
    batch = []
    for i in range(to_create):
        amount = generate_amount()
        is_anomaly = amount > 50000 or random.random() < 0.03
        anomaly_score = round(random.uniform(0.7, 0.99), 3) if is_anomaly else round(random.uniform(0.01, 0.3), 3)

        tx = Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
            amount=amount,
            currency=random.choice(CURRENCIES),
            timestamp=random_timestamp(),
            status=random.choice(STATUSES),
            meta={
                "account_id": f"ACC-{random.randint(1000, 9999)}",
                "merchant": random.choice(["Bloomberg", "Reuters", "ICE", "CME", "LSEG", "Refinitiv"]),
                "region": random.choice(["US", "EU", "APAC", "LATAM"]),
            },
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            anomaly_details={"reason": "high_amount"} if is_anomaly else None,
        )
        batch.append(tx)

        if len(batch) >= 100:
            db.add_all(batch)
            db.commit()
            batch = []

    if batch:
        db.add_all(batch)
        db.commit()

    print(f"  Transactions: {to_create} created (total: {db.query(Transaction).count()})")


def seed_compliance_logs(db):
    """Seed compliance logs."""
    existing = db.query(ComplianceLog).count()
    if existing >= NUM_COMPLIANCE_LOGS:
        print(f"  Compliance logs: {existing} already exist, skipping")
        return

    to_create = NUM_COMPLIANCE_LOGS - existing
    event_types = ["transaction", "system", "user_action"]
    descriptions = [
        "Large transaction flagged for review",
        "Failed authentication attempt detected",
        "Unusual trading pattern identified",
        "System latency exceeded threshold",
        "Compliance rule violation detected",
        "Data export requested",
        "Role permission change detected",
        "API rate limit exceeded",
        "Model drift detected above threshold",
        "Automated retraining triggered",
    ]

    for _ in range(to_create):
        db.add(ComplianceLog(
            event_type=random.choice(event_types),
            event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            timestamp=random_timestamp(),
            severity=random.choice(SEVERITIES),
            description=random.choice(descriptions),
            meta={"source": random.choice(["ml_model", "rule_engine", "manual"])},
            is_resolved=random.random() < 0.6,
            resolution_notes="Reviewed and cleared" if random.random() < 0.4 else None,
        ))
    db.commit()
    print(f"  Compliance logs: {to_create} created (total: {db.query(ComplianceLog).count()})")


def seed_system_metrics(db):
    """Seed system metrics."""
    existing = db.query(SystemMetric).count()
    if existing >= NUM_SYSTEM_METRICS:
        print(f"  System metrics: {existing} already exist, skipping")
        return

    to_create = NUM_SYSTEM_METRICS - existing
    for _ in range(to_create):
        metric_name = random.choice(METRIC_NAMES)
        if "latency" in metric_name or "time" in metric_name:
            value = round(random.uniform(5, 500), 2)
        elif "percent" in metric_name or "ratio" in metric_name:
            value = round(random.uniform(0, 100), 2)
        elif "rate" in metric_name:
            value = round(random.uniform(0, 1000), 2)
        else:
            value = round(random.uniform(0, 500), 2)

        is_anomaly = random.random() < 0.08
        db.add(SystemMetric(
            metric_name=metric_name,
            value=value,
            timestamp=random_timestamp(days_back=7),
            labels={"service": random.choice(["backend", "ml-pipeline", "otel-collector"])},
            is_anomaly=is_anomaly,
            anomaly_score=round(random.uniform(0.7, 0.95), 3) if is_anomaly else None,
        ))
    db.commit()
    print(f"  System metrics: {to_create} created (total: {db.query(SystemMetric).count()})")


def seed_incidents(db, users):
    """Seed incidents."""
    existing = db.query(Incident).count()
    if existing >= NUM_INCIDENTS:
        print(f"  Incidents: {existing} already exist, skipping")
        return

    to_create = NUM_INCIDENTS - existing
    user_ids = [u.id for u in users] if users else [None]
    incidents_to_add = []

    for _ in range(to_create):
        severity = random.choice(SEVERITIES)
        status = random.choice(INCIDENT_STATUSES)
        inc_type = random.choice(INCIDENT_TYPES)
        created = random_timestamp(days_back=14)
        inc = Incident(
            incident_id=f"INC-{uuid.uuid4().hex[:8].upper()}",
            title=f"{inc_type.replace('_', ' ').title()} detected on {random.choice(DESKS)}",
            description=f"Automated detection of {inc_type} event requiring investigation",
            severity=severity,
            status=status,
            type=inc_type,
            desk=random.choice(DESKS),
            trader=random.choice(TRADERS),
            priority=random.randint(1, 5),
            root_cause=f"Identified as {inc_type}" if status in ("resolved", "closed") else None,
            recommended_action=f"Review {inc_type} and escalate if needed",
            detection_method=random.choice(["rule", "ml", "manual"]),
            created_at=created,
            updated_at=created + timedelta(hours=random.randint(0, 48)),
            resolved_at=(created + timedelta(hours=random.randint(1, 72))) if status in ("resolved", "closed") else None,
            assigned_to=random.choice(user_ids),
            meta={"auto_detected": True, "confidence": round(random.uniform(0.6, 0.99), 2)},
        )
        db.add(inc)
        incidents_to_add.append(inc)
    db.commit()
    for inc in incidents_to_add:
        try:
            from apps.backend.services.audit_trail_service import record_audit_event
            record_audit_event(
                db=db,
                event_type="incident_created",
                entity_type="incident",
                entity_id=inc.incident_id,
                actor_type="system",
                summary=f"Incident created: {inc.title or inc.incident_id}",
                details={"type": inc.type, "severity": inc.severity, "source": "seed_data"},
                regulation_tags=["SEC_17a4"],
            )
        except Exception:
            pass
    print(f"  Incidents: {to_create} created (total: {db.query(Incident).count()})")


def main():
    print("=" * 50)
    print("Seeding database...")
    print(f"Target: {os.environ.get('DATABASE_URL', 'local default')}")
    print("=" * 50)

    db = SessionLocal()
    try:
        users = seed_users(db)
        seed_transactions(db)
        seed_compliance_logs(db)
        seed_system_metrics(db)
        seed_incidents(db, users)
        print("=" * 50)
        print("Seeding complete!")
    finally:
        db.close()


if __name__ == "__main__":
    main()
