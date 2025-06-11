"""
Kafka Consumer Service for Trading Event Ingestion
- Connects to Kafka topics (orders, executions, trades)
- Parses and normalizes events
- Passes events to anomaly detection and incident creation logic

Best practice: Run as a separate process/service for reliability and scaling.
"""

import os
import json
import time
from confluent_kafka import Consumer, KafkaException
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from apps.backend.models import Incident
from apps.backend.services.anomaly_detection_service import AnomalyDetectionService
from datetime import datetime
from apps.backend.main import incident_broadcaster

# --- CONFIGURATION ---
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092")
KAFKA_GROUP = os.getenv("KAFKA_GROUP", "fin-observability-consumer")
KAFKA_TOPICS = os.getenv("KAFKA_TOPICS", "orders,executions,trades").split(",")

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- MAIN CONSUMER LOOP ---
def main():
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BROKERS,
            "group.id": KAFKA_GROUP,
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe(KAFKA_TOPICS)
    print(f"[Kafka] Subscribed to topics: {KAFKA_TOPICS}")

    anomaly_service = AnomalyDetectionService()

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"[Kafka] Consumer error: {msg.error()}")
                continue
            try:
                event = json.loads(msg.value().decode("utf-8"))
                event_type = msg.topic()
                print(f"[Kafka] Received event from {event_type}: {event}")
                process_event(event, event_type, anomaly_service)
            except Exception as e:
                print(f"[Kafka] Failed to process message: {e}")
    except KeyboardInterrupt:
        print("[Kafka] Stopping consumer...")
    finally:
        consumer.close()


# --- EVENT PROCESSING & INCIDENT CREATION ---
def process_event(event, event_type, anomaly_service):
    # Normalize event (customize this for your trading system schema)
    # Example fields: order_id, trader, desk, status, timestamp, etc.
    normalized = {
        "event_id": event.get("order_id") or event.get("trade_id") or event.get("id"),
        "desk": event.get("desk", "unknown"),
        "trader": event.get("trader", "unknown"),
        "timestamp": event.get("timestamp", datetime.utcnow().isoformat()),
        "status": event.get("status", ""),
        "raw": event,
    }

    # --- Anomaly Detection (simple rule-based, can extend to ML) ---
    incident_type = None
    root_cause = None
    recommended_action = None
    priority = 2

    # Example: Stuck order
    if event_type == "orders" and normalized["status"] == "pending":
        # TODO: Add logic to check if order is stuck (e.g., time in state > threshold)
        incident_type = "stuck_order"
        root_cause = "Order in pending state too long."
        recommended_action = "Investigate order routing and connectivity."
        priority = 1
    # Example: Missed trade
    elif (
        event_type == "trades"
        and event.get("expected_fill")
        and not event.get("actual_fill")
    ):
        incident_type = "missed_trade"
        root_cause = "Expected fill not received."
        recommended_action = "Check counterparty and liquidity."
        priority = 1
    # Example: Spike
    elif event_type == "executions" and event.get("volume_spike", False):
        incident_type = "spike"
        root_cause = "Unusual volume spike detected."
        recommended_action = "Review market conditions."
        priority = 2
    # TODO: Add more sophisticated/ML-based anomaly detection here.

    if incident_type:
        db = SessionLocal()
        try:
            incident = Incident(
                incident_id=f"{incident_type}-{normalized['event_id']}-{int(time.time())}",
                title=f"{incident_type.replace('_', ' ').title()} detected",
                description=f"Auto-detected {incident_type} for event {normalized['event_id']}",
                severity="high" if priority == 1 else "medium",
                type=incident_type,
                desk=normalized["desk"],
                trader=normalized["trader"],
                priority=priority,
                root_cause=root_cause,
                recommended_action=recommended_action,
                source_event_id=normalized["event_id"],
                detection_method="rule",
                last_event_timestamp=datetime.fromisoformat(normalized["timestamp"]),
                status="open",
                meta=normalized["raw"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(incident)
            db.commit()
            print(f"[Kafka] Incident created: {incident.incident_id}")
            # Broadcast to WebSocket clients
            import asyncio

            asyncio.create_task(
                incident_broadcaster.broadcast(
                    json.dumps(
                        {
                            c.name: getattr(incident, c.name)
                            for c in Incident.__table__.columns
                        }
                    )
                )
            )
        except Exception as e:
            db.rollback()
            print(f"[Kafka] Failed to create incident: {e}")
        finally:
            db.close()


if __name__ == "__main__":
    main()
