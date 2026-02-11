"""
Generate a realistic anonymized financial transaction dataset for model training.
Produces a CSV with configurable size (default: 1,000,000 transactions).

Enhanced features:
- Temporal patterns: quarter-end spikes, month-end surges, holiday lulls
- Account behavior profiles: each account has a "normal" baseline
- Geographic risk scoring: high-risk jurisdictions
- Velocity features: transaction frequency per account per day
- Configurable via DATASET_SIZE env var (default: 1000000)
- Batch CSV writing for memory efficiency at scale
"""
import csv
import os
import random
import math
from datetime import datetime, timedelta
from collections import defaultdict
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

DEFAULT_DATASET_SIZE = int(os.environ.get("DATASET_SIZE", "1000000"))
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "transactions.csv")

# Distribution parameters based on real financial patterns
NORMAL_WEIGHT = 0.82
SUSPICIOUS_WEIGHT = 0.12
VIOLATION_WEIGHT = 0.06

COUNTERPARTIES_NORMAL = [
    "Acme Corp", "GlobalTech Inc", "Meridian Partners", "Atlas Financial",
    "Pinnacle Holdings", "Summit Capital", "Vanguard Services", "Horizon Group",
    "Sterling Industries", "Pacific Trading Co", "Nordic Ventures", "Apex Solutions",
    "Blue Ridge Capital", "Coastal Ventures", "Delta Systems", "Eagle Partners",
]
COUNTERPARTIES_SUSPICIOUS = [
    "Offshore Holdings Ltd", "Unknown Entity LLC", "Shell Corp International",
    "Rapid Transfer SA", "Unnamed Trust", "Anonymous Trading BVI",
    "Cayman Investments Ltd", "Panama Global SA",
]

JURISDICTIONS_LOW_RISK = ["US", "UK", "DE", "JP", "CA", "AU", "FR", "CH"]
JURISDICTIONS_MEDIUM_RISK = ["BR", "IN", "MX", "ZA", "TR", "AE"]
JURISDICTIONS_HIGH_RISK = ["KY", "PA", "VG", "BZ", "VU", "WS"]

# Account profiles: each account has a typical amount range and preferred hours
ACCOUNT_PROFILES = {}


def _get_account_profile(account_id: str) -> dict:
    """Get or create a behavioral profile for an account."""
    if account_id not in ACCOUNT_PROFILES:
        ACCOUNT_PROFILES[account_id] = {
            "typical_amount_mean": random.lognormvariate(7.2, 1.0),
            "typical_amount_std": random.uniform(0.3, 0.8),
            "preferred_hour": int(random.gauss(13, 2)),
            "preferred_types": random.choices(
                [["ach", "internal", "wire"], ["wire", "ach"], ["internal", "ach"]],
                weights=[0.6, 0.25, 0.15],
            )[0],
            "jurisdiction": random.choices(
                JURISDICTIONS_LOW_RISK + JURISDICTIONS_MEDIUM_RISK,
                weights=[5]*8 + [2]*6,
            )[0],
            "account_age_days": random.randint(30, 3650),
        }
    return ACCOUNT_PROFILES[account_id]


def _is_quarter_end(date: datetime) -> bool:
    return date.month in (3, 6, 9, 12) and date.day >= 25


def _is_month_end(date: datetime) -> bool:
    return date.day >= 27


def _seasonal_amount_multiplier(date: datetime) -> float:
    """Quarter-end and month-end surges."""
    mult = 1.0
    if _is_quarter_end(date):
        mult *= random.uniform(1.3, 2.0)
    elif _is_month_end(date):
        mult *= random.uniform(1.1, 1.4)
    return mult


def generate_normal_transaction(base_date: datetime, account_id: str) -> dict:
    """Normal business transaction during business hours."""
    profile = _get_account_profile(account_id)
    amount = random.lognormvariate(
        math.log(max(profile["typical_amount_mean"], 50)),
        profile["typical_amount_std"],
    )
    amount = max(50, min(amount, 15000))
    amount *= _seasonal_amount_multiplier(base_date)
    hour = int(random.gauss(profile["preferred_hour"], 2.5))
    hour = max(8, min(hour, 18))
    day_offset = random.randint(0, 4)  # Weekday
    ts = base_date + timedelta(days=day_offset, hours=hour, minutes=random.randint(0, 59))
    return {
        "amount": round(amount, 2),
        "counterparty": random.choice(COUNTERPARTIES_NORMAL),
        "type": random.choice(profile["preferred_types"]),
        "timestamp": ts.isoformat(),
        "label": "normal",
        "jurisdiction": profile["jurisdiction"],
        "account_age_days": profile["account_age_days"],
    }


def generate_suspicious_transaction(base_date: datetime, account_id: str) -> dict:
    """Suspicious: large amounts, off-hours, weekends, high-risk jurisdictions."""
    profile = _get_account_profile(account_id)
    # Deviate significantly from account's normal pattern
    amount = profile["typical_amount_mean"] * random.uniform(3, 10)
    amount = max(10000, min(amount, 75000))
    amount *= _seasonal_amount_multiplier(base_date)
    hour = random.choice([random.randint(0, 5), random.randint(22, 23)])
    day_offset = random.choice([5, 6]) if random.random() < 0.6 else random.randint(0, 4)
    ts = base_date + timedelta(days=day_offset, hours=hour, minutes=random.randint(0, 59))
    jurisdiction = random.choices(
        JURISDICTIONS_HIGH_RISK + JURISDICTIONS_MEDIUM_RISK,
        weights=[4]*6 + [1]*6,
    )[0]
    return {
        "amount": round(amount, 2),
        "counterparty": random.choice(COUNTERPARTIES_SUSPICIOUS),
        "type": random.choices(["wire", "ach"], weights=[0.7, 0.3])[0],
        "timestamp": ts.isoformat(),
        "label": "suspicious",
        "jurisdiction": jurisdiction,
        "account_age_days": random.randint(1, 90),  # Often new accounts
    }


def generate_violation_transaction(base_date: datetime, account_id: str) -> dict:
    """Violation: extremely large, regulatory threshold breach."""
    amount = random.uniform(100000, 500000)
    hour = random.randint(0, 23)
    day_offset = random.randint(0, 6)
    ts = base_date + timedelta(days=day_offset, hours=hour, minutes=random.randint(0, 59))
    jurisdiction = random.choice(JURISDICTIONS_HIGH_RISK)
    return {
        "amount": round(amount, 2),
        "counterparty": random.choice(COUNTERPARTIES_SUSPICIOUS),
        "type": "wire",
        "timestamp": ts.isoformat(),
        "label": "violation",
        "jurisdiction": jurisdiction,
        "account_age_days": random.randint(1, 30),
    }


def _compute_velocity(transactions: list) -> list:
    """Compute daily transaction count per account (velocity feature)."""
    daily_counts = defaultdict(lambda: defaultdict(int))
    for txn in transactions:
        day_key = txn["timestamp"][:10]
        daily_counts[txn["account"]][day_key] += 1

    for txn in transactions:
        day_key = txn["timestamp"][:10]
        txn["daily_txn_count"] = daily_counts[txn["account"]][day_key]
    return transactions


def generate_dataset(n_samples: int = DEFAULT_DATASET_SIZE) -> list:
    """Generate full dataset with realistic class distribution and behavioral profiles."""
    transactions = []
    base_date = datetime(2024, 1, 1)
    # Scale account pool with dataset size (5K accounts for 1M transactions)
    n_accounts = max(200, min(n_samples // 200, 5000))
    account_pool = [fake.bban() for _ in range(n_accounts)]

    for i in range(n_samples):
        week_offset = (i // 1000) * 7  # Spread across weeks
        week_base = base_date + timedelta(days=week_offset % 730)  # 2 years of data
        account = random.choice(account_pool)

        r = random.random()
        if r < NORMAL_WEIGHT:
            txn = generate_normal_transaction(week_base, account)
        elif r < NORMAL_WEIGHT + SUSPICIOUS_WEIGHT:
            txn = generate_suspicious_transaction(week_base, account)
        else:
            txn = generate_violation_transaction(week_base, account)

        txn["id"] = f"txn_{i:07d}"
        txn["account"] = account
        transactions.append(txn)

    # Compute velocity features
    transactions = _compute_velocity(transactions)
    return transactions


FIELDNAMES = [
    "id", "amount", "counterparty", "account", "type", "timestamp",
    "label", "jurisdiction", "account_age_days", "daily_txn_count",
]


def write_csv(transactions: list, path: str = OUTPUT_PATH):
    """Write transactions to CSV."""
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(transactions)
    print(f"Generated {len(transactions)} transactions -> {path}")


def generate_and_write_batched(
    n_samples: int = DEFAULT_DATASET_SIZE,
    batch_size: int = 50000,
    path: str = OUTPUT_PATH,
):
    """
    Generate and write dataset in batches for memory efficiency at scale.
    Writes directly to CSV without holding entire dataset in memory.
    Velocity features are computed per-batch (approximate but scalable).
    """
    import time
    start = time.time()
    base_date = datetime(2024, 1, 1)
    n_accounts = max(200, min(n_samples // 200, 5000))
    account_pool = [fake.bban() for _ in range(n_accounts)]

    total_written = 0
    label_counts = defaultdict(int)

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for batch_start in range(0, n_samples, batch_size):
            batch_end = min(batch_start + batch_size, n_samples)
            batch = []

            for i in range(batch_start, batch_end):
                week_offset = (i // 1000) * 7
                week_base = base_date + timedelta(days=week_offset % 730)
                account = random.choice(account_pool)

                r = random.random()
                if r < NORMAL_WEIGHT:
                    txn = generate_normal_transaction(week_base, account)
                elif r < NORMAL_WEIGHT + SUSPICIOUS_WEIGHT:
                    txn = generate_suspicious_transaction(week_base, account)
                else:
                    txn = generate_violation_transaction(week_base, account)

                txn["id"] = f"txn_{i:07d}"
                txn["account"] = account
                label_counts[txn["label"]] += 1
                batch.append(txn)

            # Compute velocity within batch
            batch = _compute_velocity(batch)
            writer.writerows(batch)
            total_written += len(batch)

            elapsed = time.time() - start
            pct = (total_written / n_samples) * 100
            print(f"  [{pct:5.1f}%] Written {total_written:,} / {n_samples:,} ({elapsed:.1f}s)")

    elapsed = time.time() - start
    print(f"\nGenerated {total_written:,} transactions -> {path} ({elapsed:.1f}s)")
    print(f"Distribution: {dict(label_counts)}")
    file_size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"File size: {file_size_mb:.1f} MB")
    return total_written


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATASET_SIZE
    print(f"Generating {n:,} transactions...")
    generate_and_write_batched(n)
