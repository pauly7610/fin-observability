"""
Load test script for fin-observability backend.
Generates realistic traffic patterns across all major endpoints.

Usage:
    python scripts/load_test.py                          # default: 100 requests
    python scripts/load_test.py --requests 500           # custom count
    python scripts/load_test.py --base-url http://localhost:8080
    python scripts/load_test.py --concurrency 10         # parallel workers

Requires: pip install requests
"""

import argparse
import json
import random
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

# --- Endpoint definitions ---
ENDPOINTS = [
    {"method": "GET", "path": "/health", "weight": 15},
    {"method": "GET", "path": "/transactions", "weight": 20},
    {"method": "GET", "path": "/auth/roles", "weight": 5},
    {"method": "GET", "path": "/compliance", "weight": 10},
    {"method": "GET", "path": "/incidents", "weight": 10},
    {"method": "GET", "path": "/system-metrics", "weight": 5},
    {"method": "POST", "path": "/transactions", "weight": 25, "body": "transaction"},
    {"method": "GET", "path": "/agent/compliance/drift/status", "weight": 5, "auth": True},
    {"method": "GET", "path": "/agent/compliance/retrain/status", "weight": 5, "auth": True},
    {"method": "POST", "path": "/agent/compliance/monitor", "weight": 10, "body": "compliance_monitor", "auth": True},
    {"method": "POST", "path": "/anomaly/detect", "weight": 5, "body": "anomaly_detect"},
]

CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF"]
STATUSES = ["completed", "completed", "completed", "pending", "failed"]


def weighted_choice(endpoints):
    total = sum(e["weight"] for e in endpoints)
    r = random.uniform(0, total)
    cumulative = 0
    for ep in endpoints:
        cumulative += ep["weight"]
        if r <= cumulative:
            return ep
    return endpoints[-1]


def generate_transaction_body():
    amount = round(random.uniform(10, 50000), 2)
    if random.random() < 0.05:
        amount = round(random.uniform(100000, 500000), 2)
    return {
        "transaction_id": f"LT-{uuid.uuid4().hex[:12].upper()}",
        "amount": amount,
        "currency": random.choice(CURRENCIES),
        "status": random.choice(STATUSES),
        "meta": {
            "account_id": f"ACC-{random.randint(1000, 9999)}",
            "merchant": random.choice(["Bloomberg", "Reuters", "ICE", "CME"]),
            "region": random.choice(["US", "EU", "APAC"]),
            "load_test": True,
        },
    }


def generate_anomaly_detect_body():
    data = []
    for _ in range(random.randint(1, 5)):
        amount = round(random.uniform(10, 50000), 2)
        if random.random() < 0.1:
            amount = round(random.uniform(200000, 1000000), 2)
        data.append({
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "currency": random.choice(CURRENCIES),
            "type": random.choice(["wire", "ach", "check", "internal"]),
        })
    return {"data": data, "model_type": "isolation_forest"}


def generate_compliance_body():
    amount = round(random.uniform(100, 200000), 2)
    if random.random() < 0.1:
        amount = round(random.uniform(500000, 2000000), 2)
    return {
        "id": f"CM-{uuid.uuid4().hex[:12].upper()}",
        "amount": amount,
        "counterparty": random.choice(["ACME Corp", "Goldman Sachs", "JPMorgan", "Citadel", "Two Sigma"]),
        "account": f"{random.randint(1000000000, 9999999999)}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": random.choice(["wire", "ach", "check", "internal"]),
    }


def make_request(base_url, endpoint):
    url = f"{base_url}{endpoint['path']}"
    headers = {"Content-Type": "application/json"}

    if endpoint.get("auth"):
        headers["x-user-email"] = "admin@finobs.io"
        headers["x-user-role"] = "admin"

    start = time.time()
    try:
        if endpoint["method"] == "GET":
            resp = requests.get(url, headers=headers, timeout=10)
        elif endpoint["method"] == "POST":
            if endpoint.get("body") == "transaction":
                body = generate_transaction_body()
            elif endpoint.get("body") == "compliance_monitor":
                body = generate_compliance_body()
            elif endpoint.get("body") == "anomaly_detect":
                body = generate_anomaly_detect_body()
            else:
                body = {}
            resp = requests.post(url, json=body, headers=headers, timeout=10)
        else:
            return None

        duration_ms = round((time.time() - start) * 1000, 1)
        return {
            "method": endpoint["method"],
            "path": endpoint["path"],
            "status": resp.status_code,
            "duration_ms": duration_ms,
            "success": resp.status_code < 500,
        }
    except requests.exceptions.RequestException as e:
        duration_ms = round((time.time() - start) * 1000, 1)
        return {
            "method": endpoint["method"],
            "path": endpoint["path"],
            "status": 0,
            "duration_ms": duration_ms,
            "success": False,
            "error": str(e)[:100],
        }


def run_load_test(base_url, num_requests, concurrency):
    print(f"{'=' * 60}")
    print(f"Load Test: {base_url}")
    print(f"Requests: {num_requests} | Concurrency: {concurrency}")
    print(f"Started: {datetime.utcnow().isoformat()}Z")
    print(f"{'=' * 60}")

    results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for _ in range(num_requests):
            ep = weighted_choice(ENDPOINTS)
            futures.append(executor.submit(make_request, base_url, ep))

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result:
                results.append(result)
            if i % 50 == 0 or i == num_requests:
                elapsed = time.time() - start_time
                rps = i / elapsed if elapsed > 0 else 0
                print(f"  Progress: {i}/{num_requests} ({rps:.1f} req/s)")

    total_time = time.time() - start_time

    # --- Summary ---
    successes = sum(1 for r in results if r["success"])
    failures = len(results) - successes
    durations = [r["duration_ms"] for r in results]
    durations.sort()

    status_counts = {}
    for r in results:
        code = r["status"]
        status_counts[code] = status_counts.get(code, 0) + 1

    endpoint_stats = {}
    for r in results:
        key = f"{r['method']} {r['path']}"
        if key not in endpoint_stats:
            endpoint_stats[key] = {"count": 0, "durations": [], "errors": 0}
        endpoint_stats[key]["count"] += 1
        endpoint_stats[key]["durations"].append(r["duration_ms"])
        if not r["success"]:
            endpoint_stats[key]["errors"] += 1

    print(f"\n{'=' * 60}")
    print(f"RESULTS")
    print(f"{'=' * 60}")
    print(f"Total time:    {total_time:.1f}s")
    print(f"Requests:      {len(results)}")
    print(f"Successes:     {successes} ({successes/len(results)*100:.1f}%)")
    print(f"Failures:      {failures}")
    print(f"Throughput:    {len(results)/total_time:.1f} req/s")
    print(f"Avg latency:   {sum(durations)/len(durations):.1f}ms")
    print(f"P50 latency:   {durations[len(durations)//2]:.1f}ms")
    print(f"P95 latency:   {durations[int(len(durations)*0.95)]:.1f}ms")
    print(f"P99 latency:   {durations[int(len(durations)*0.99)]:.1f}ms")
    print(f"Max latency:   {max(durations):.1f}ms")

    print(f"\nStatus codes:")
    for code, count in sorted(status_counts.items()):
        print(f"  {code}: {count}")

    print(f"\nEndpoint breakdown:")
    for ep, stats in sorted(endpoint_stats.items(), key=lambda x: -x[1]["count"]):
        avg = sum(stats["durations"]) / len(stats["durations"])
        p95 = sorted(stats["durations"])[int(len(stats["durations"]) * 0.95)] if len(stats["durations"]) > 1 else stats["durations"][0]
        err = f" ({stats['errors']} errors)" if stats["errors"] else ""
        print(f"  {ep:40s} {stats['count']:4d} reqs  avg={avg:.0f}ms  p95={p95:.0f}ms{err}")

    print(f"\n{'=' * 60}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load test fin-observability backend")
    parser.add_argument("--base-url", default="https://fin-observability-production.up.railway.app", help="Base URL")
    parser.add_argument("--requests", type=int, default=200, help="Number of requests")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrent workers")
    args = parser.parse_args()

    run_load_test(args.base_url, args.requests, args.concurrency)
