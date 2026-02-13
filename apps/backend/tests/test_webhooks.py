"""
Comprehensive tests for the webhook system:
- Inbound webhook ingestion (single + batch)
- SSE streaming (EventBus)
- Outbound webhook notifications (OutboundNotifier + DLQ)
- Scheduled pull ingestion (PullIngestionConfig)
- MCP ingest_transactions tool
- Results retrieval
- Callback management
- System status
"""
from apps.backend.main import app
from apps.backend.routers.webhooks import (
    EventBus,
    OutboundNotifier,
    PullIngestionConfig,
    score_and_store_transaction,
    event_bus,
    outbound_notifier,
)
from apps.backend.database import SessionLocal
from fastapi.testclient import TestClient
import pytest
import asyncio
import json

client = TestClient(app)

ADMIN_HEADERS = {
    "x-user-email": "admin@example.com",
    "x-user-role": "admin",
}

WEBHOOK_HEADERS = {"X-Webhook-Key": "test-webhook-key"}


# ---------------------------------------------------------------------------
# Inbound webhook ingestion
# ---------------------------------------------------------------------------
class TestWebhookIngestion:
    def test_single_transaction(self):
        resp = client.post(
            "/webhooks/transactions",
            json={"amount": 5000, "type": "wire_transfer", "transaction_id": f"test-single-{id(self)}"},
            headers=WEBHOOK_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ingested"] == 1
        assert data["results"][0]["decision"] in ("approve", "manual_review")
        assert data["results"][0]["stored"] is True

    def test_batch_transactions(self):
        txns = [
            {"amount": 100 + i, "type": "ach", "transaction_id": f"test-batch-{id(self)}-{i}"}
            for i in range(5)
        ]
        resp = client.post("/webhooks/transactions", json=txns, headers=WEBHOOK_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["ingested"] == 5
        assert len(data["results"]) == 5
        assert data["total_amount"] > 0

    def test_empty_body_rejected(self):
        resp = client.post(
            "/webhooks/transactions",
            content='"not an object or list"',
            headers={**WEBHOOK_HEADERS, "content-type": "application/json"},
        )
        assert resp.status_code == 400

    def test_invalid_amount(self):
        resp = client.post(
            "/webhooks/transactions",
            json={"amount": -100, "transaction_id": f"test-neg-{id(self)}"},
            headers=WEBHOOK_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data["results"][0]

    def test_auto_generated_transaction_id(self):
        resp = client.post(
            "/webhooks/transactions",
            json={"amount": 999},
            headers=WEBHOOK_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"][0]["transaction_id"].startswith("webhook-")

    def test_non_dict_in_batch(self):
        resp = client.post(
            "/webhooks/transactions",
            json=[{"amount": 100}, "not a dict", {"amount": 200}],
            headers=WEBHOOK_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ingested"] == 3
        assert "error" in data["results"][1]


# ---------------------------------------------------------------------------
# Results retrieval
# ---------------------------------------------------------------------------
class TestWebhookResults:
    def test_get_results(self):
        # Ingest first
        client.post(
            "/webhooks/transactions",
            json={"amount": 7777, "transaction_id": f"test-results-{id(self)}"},
            headers=WEBHOOK_HEADERS,
        )
        resp = client.get("/webhooks/results", headers=WEBHOOK_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "results" in data

    def test_get_results_with_limit(self):
        resp = client.get("/webhooks/results?limit=2", headers=WEBHOOK_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] <= 2

    def test_get_results_flagged_only(self):
        resp = client.get("/webhooks/results?flagged_only=true", headers=WEBHOOK_HEADERS)
        assert resp.status_code == 200

    def test_get_results_by_source(self):
        resp = client.get("/webhooks/results?source=webhook", headers=WEBHOOK_HEADERS)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# EventBus (SSE infrastructure)
# ---------------------------------------------------------------------------
class TestEventBus:
    def test_publish_and_recent(self):
        bus = EventBus()
        bus.publish({"test": 1})
        bus.publish({"test": 2})
        recent = bus.get_recent()
        assert len(recent) == 2
        assert recent[0]["test"] == 1

    def test_subscribe_and_receive(self):
        bus = EventBus()
        q = bus.subscribe()
        assert bus.subscriber_count == 1
        bus.publish({"msg": "hello"})

        loop = asyncio.new_event_loop()
        event = loop.run_until_complete(asyncio.wait_for(q.get(), timeout=1.0))
        loop.close()
        assert event["msg"] == "hello"

    def test_unsubscribe(self):
        bus = EventBus()
        q = bus.subscribe()
        assert bus.subscriber_count == 1
        bus.unsubscribe(q)
        assert bus.subscriber_count == 0

    def test_full_queue_drops_subscriber(self):
        bus = EventBus()
        q = bus.subscribe()
        # Fill the queue (maxsize=256)
        for i in range(300):
            bus.publish({"i": i})
        # Subscriber should have been dropped
        assert bus.subscriber_count == 0

    def test_recent_capped_at_50(self):
        bus = EventBus()
        for i in range(100):
            bus.publish({"i": i})
        assert len(bus.get_recent()) == 50


# ---------------------------------------------------------------------------
# SSE stream endpoint
# ---------------------------------------------------------------------------
class TestSSEStream:
    def test_stream_status(self):
        resp = client.get("/webhooks/stream/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "subscribers" in data
        assert "recent_events" in data


# ---------------------------------------------------------------------------
# Outbound webhook notifications
# ---------------------------------------------------------------------------
class TestOutboundNotifier:
    def test_register_and_list_callbacks(self):
        notifier = OutboundNotifier()
        notifier.register_callback("https://example.com/hook1")
        notifier.register_callback("https://example.com/hook2")
        assert len(notifier.list_callbacks()) == 2

    def test_no_duplicate_callbacks(self):
        notifier = OutboundNotifier()
        notifier.register_callback("https://example.com/hook")
        notifier.register_callback("https://example.com/hook")
        assert len(notifier.list_callbacks()) == 1

    def test_remove_callback(self):
        notifier = OutboundNotifier()
        notifier.register_callback("https://example.com/hook")
        notifier.remove_callback("https://example.com/hook")
        assert len(notifier.list_callbacks()) == 0

    def test_dead_letter_queue_empty(self):
        notifier = OutboundNotifier()
        assert notifier.get_dead_letter() == []

    def test_delivery_log_empty(self):
        notifier = OutboundNotifier()
        assert notifier.get_delivery_log() == []


class TestCallbackEndpoints:
    def test_register_callback_endpoint(self):
        resp = client.post(
            "/webhooks/callbacks",
            json={"url": "https://test-callback.example.com/hook"},
            headers=WEBHOOK_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["registered"] == "https://test-callback.example.com/hook"

    def test_register_callback_invalid_url(self):
        resp = client.post(
            "/webhooks/callbacks",
            json={"url": "not-a-url"},
            headers=WEBHOOK_HEADERS,
        )
        assert resp.status_code == 400

    def test_register_callback_missing_url(self):
        resp = client.post(
            "/webhooks/callbacks",
            json={"name": "test"},
            headers=WEBHOOK_HEADERS,
        )
        assert resp.status_code == 400

    def test_list_callbacks_endpoint(self):
        resp = client.get("/webhooks/callbacks", headers=WEBHOOK_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "callbacks" in data
        assert "delivery_log" in data

    def test_dlq_endpoint(self):
        resp = client.get("/webhooks/callbacks/dlq", headers=WEBHOOK_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "items" in data


# ---------------------------------------------------------------------------
# Pull ingestion
# ---------------------------------------------------------------------------
class TestPullIngestion:
    def test_add_source(self):
        config = PullIngestionConfig()
        source = config.add_source({"name": "test-api", "url": "https://api.example.com/txns"})
        assert "id" in source
        assert source["interval_seconds"] == 300
        assert source["enabled"] is True

    def test_add_source_missing_fields(self):
        config = PullIngestionConfig()
        with pytest.raises(ValueError):
            config.add_source({"name": "test-api"})  # missing url

    def test_remove_source(self):
        config = PullIngestionConfig()
        source = config.add_source({"name": "test-api", "url": "https://api.example.com/txns"})
        assert config.remove_source(source["id"]) is True
        assert len(config.list_sources()) == 0

    def test_remove_nonexistent_source(self):
        config = PullIngestionConfig()
        assert config.remove_source("nonexistent") is False

    def test_list_sources_redacts_headers(self):
        config = PullIngestionConfig()
        config.add_source({
            "name": "test-api",
            "url": "https://api.example.com/txns",
            "headers": {"Authorization": "Bearer secret"},
        })
        sources = config.list_sources()
        assert len(sources) == 1
        assert "headers" not in sources[0]


class TestPullIngestionEndpoints:
    def test_add_source_endpoint(self):
        resp = client.post(
            "/webhooks/pull/sources",
            json={"name": "test-endpoint-src", "url": "https://api.example.com/transactions"},
            headers=WEBHOOK_HEADERS,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "added" in data
        assert data["added"]["name"] == "test-endpoint-src"

    def test_add_source_missing_url(self):
        resp = client.post(
            "/webhooks/pull/sources",
            json={"name": "bad-source"},
            headers=WEBHOOK_HEADERS,
        )
        assert resp.status_code == 400

    def test_list_sources_endpoint(self):
        resp = client.get("/webhooks/pull/sources", headers=WEBHOOK_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data
        assert "results" in data

    def test_trigger_nonexistent_source(self):
        resp = client.post("/webhooks/pull/trigger/nonexistent", headers=WEBHOOK_HEADERS)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Shared scoring pipeline
# ---------------------------------------------------------------------------
class TestScoringPipeline:
    def test_score_and_store(self):
        db = SessionLocal()
        try:
            result = score_and_store_transaction(
                {"amount": 12345, "type": "ach", "transaction_id": f"test-pipeline-{id(self)}"},
                source="test",
                db=db,
            )
            assert result["stored"] is True
            assert result["decision"] in ("approve", "manual_review")
            assert result["anomaly_score"] >= 0
            assert result["source"] == "test"
        finally:
            db.close()

    def test_score_negative_amount(self):
        db = SessionLocal()
        try:
            result = score_and_store_transaction(
                {"amount": -50, "transaction_id": "test-neg"},
                source="test",
                db=db,
            )
            assert "error" in result
        finally:
            db.close()

    def test_score_zero_amount(self):
        db = SessionLocal()
        try:
            result = score_and_store_transaction(
                {"amount": 0, "transaction_id": "test-zero"},
                source="test",
                db=db,
            )
            assert "error" in result
        finally:
            db.close()

    def test_score_with_bad_timestamp(self):
        db = SessionLocal()
        try:
            result = score_and_store_transaction(
                {"amount": 100, "timestamp": "not-a-date", "transaction_id": f"test-badts-{id(self)}"},
                source="test",
                db=db,
            )
            # Should still succeed, falling back to utcnow
            assert result["stored"] is True
        finally:
            db.close()


# ---------------------------------------------------------------------------
# System status
# ---------------------------------------------------------------------------
class TestWebhookSystemStatus:
    def test_status_endpoint(self):
        resp = client.get("/webhooks/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "sse_stream" in data
        assert "outbound_notifications" in data
        assert "pull_ingestion" in data
        assert "subscribers" in data["sse_stream"]
        assert "callbacks" in data["outbound_notifications"]
        assert "dead_letter_queue" in data["outbound_notifications"]
        assert "sources" in data["pull_ingestion"]
