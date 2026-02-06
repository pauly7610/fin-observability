"""
Generate a realistic anonymized financial transaction dataset for model training.
Produces a CSV with ~5000 transactions following real-world distributions.
"""
import csv
import os
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "transactions.csv")

# Distribution parameters based on real financial patterns
NORMAL_WEIGHT = 0.85
SUSPICIOUS_WEIGHT = 0.10
VIOLATION_WEIGHT = 0.05

COUNTERPARTIES_NORMAL = [
    "Acme Corp", "GlobalTech Inc", "Meridian Partners", "Atlas Financial",
    "Pinnacle Holdings", "Summit Capital", "Vanguard Services", "Horizon Group",
    "Sterling Industries", "Pacific Trading Co", "Nordic Ventures", "Apex Solutions",
]
COUNTERPARTIES_SUSPICIOUS = [
    "Offshore Holdings Ltd", "Unknown Entity LLC", "Shell Corp International",
    "Rapid Transfer SA", "Unnamed Trust", "Anonymous Trading BVI",
]


def generate_normal_transaction(base_date: datetime) -> dict:
    """Normal business transaction during business hours."""
    amount = random.lognormvariate(7.5, 0.8)
    amount = max(50, min(amount, 15000))
    hour = int(random.gauss(13, 2.5))
    hour = max(8, min(hour, 18))
    day_offset = random.randint(0, 4)  # Weekday
    ts = base_date + timedelta(days=day_offset, hours=hour, minutes=random.randint(0, 59))
    return {
        "amount": round(amount, 2),
        "counterparty": random.choice(COUNTERPARTIES_NORMAL),
        "type": random.choices(["ach", "internal", "wire"], weights=[0.5, 0.3, 0.2])[0],
        "timestamp": ts.isoformat(),
        "label": "normal",
    }


def generate_suspicious_transaction(base_date: datetime) -> dict:
    """Suspicious: large amounts, off-hours, weekends."""
    amount = random.uniform(10000, 75000)
    hour = random.choice([random.randint(0, 5), random.randint(22, 23)])
    day_offset = random.choice([5, 6]) if random.random() < 0.6 else random.randint(0, 4)
    ts = base_date + timedelta(days=day_offset, hours=hour, minutes=random.randint(0, 59))
    return {
        "amount": round(amount, 2),
        "counterparty": random.choice(COUNTERPARTIES_SUSPICIOUS),
        "type": random.choices(["wire", "ach"], weights=[0.7, 0.3])[0],
        "timestamp": ts.isoformat(),
        "label": "suspicious",
    }


def generate_violation_transaction(base_date: datetime) -> dict:
    """Violation: extremely large, regulatory threshold breach."""
    amount = random.uniform(100000, 500000)
    hour = random.randint(0, 23)
    day_offset = random.randint(0, 6)
    ts = base_date + timedelta(days=day_offset, hours=hour, minutes=random.randint(0, 59))
    return {
        "amount": round(amount, 2),
        "counterparty": random.choice(COUNTERPARTIES_SUSPICIOUS),
        "type": "wire",
        "timestamp": ts.isoformat(),
        "label": "violation",
    }


def generate_dataset(n_samples: int = 5000) -> list:
    """Generate full dataset with realistic class distribution."""
    transactions = []
    base_date = datetime(2024, 1, 1)

    for i in range(n_samples):
        week_offset = (i // 50) * 7  # Spread across weeks
        week_base = base_date + timedelta(days=week_offset)

        r = random.random()
        if r < NORMAL_WEIGHT:
            txn = generate_normal_transaction(week_base)
        elif r < NORMAL_WEIGHT + SUSPICIOUS_WEIGHT:
            txn = generate_suspicious_transaction(week_base)
        else:
            txn = generate_violation_transaction(week_base)

        txn["id"] = f"txn_{i:05d}"
        txn["account"] = fake.bban()
        transactions.append(txn)

    return transactions


def write_csv(transactions: list, path: str = OUTPUT_PATH):
    """Write transactions to CSV."""
    fieldnames = ["id", "amount", "counterparty", "account", "type", "timestamp", "label"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
    print(f"Generated {len(transactions)} transactions -> {path}")


if __name__ == "__main__":
    txns = generate_dataset(5000)
    write_csv(txns)

    # Print distribution summary
    from collections import Counter
    labels = Counter(t["label"] for t in txns)
    print(f"Distribution: {dict(labels)}")
    amounts = [t["amount"] for t in txns]
    print(f"Amount range: ${min(amounts):,.2f} - ${max(amounts):,.2f}")
    print(f"Mean amount: ${sum(amounts)/len(amounts):,.2f}")
