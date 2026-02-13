# MCP Design

This document describes the Model Context Protocol (MCP) integration for the Financial AI Observability Platform.

---

## Overview

The MCP server exposes compliance monitoring, anomaly detection, explainability, and metrics as tools that any MCP-compatible AI agent can connect to. It runs at `/mcp` using Streamable HTTP transport.

---

## Auth

- **MCP_API_KEY:** When set, AI clients must pass it:
  - Header: `X-MCP-API-Key: <key>`
  - Or: `Authorization: Bearer <key>`
- **Dashboard endpoints** (`/mcp/stats`, `/mcp/tools`): Require normal user auth (Clerk JWT or headers).

---

## Tools (9 total)

| Tool                           | Description                                                                |
| ------------------------------ | -------------------------------------------------------------------------- |
| `check_transaction_compliance` | Score a transaction — approve/review decision, anomaly score, risk factors |
| `explain_transaction`          | SHAP-based feature importance for a prediction                             |
| `batch_check_compliance`       | Score up to 10,000 transactions in one call                                |
| `analyze_portfolio`            | Aggregate risk: distribution, top flagged, concentration warnings          |
| `ingest_transactions`          | Push up to 10,000 transactions for scoring + storage                       |
| `get_compliance_metrics`       | Real-time approval rates, confidence scores, model info                    |
| `list_incidents`               | Browse incidents with status/severity filters                              |
| `get_drift_status`             | PSI + KS test results and retrain recommendations                          |
| `get_model_leaderboard`        | Model versions ranked by F1 score                                          |

---

## Tool Parameters

### check_transaction_compliance

- `amount` (float, required): Transaction amount in USD
- `transaction_type` (str, default: "wire_transfer"): One of wire_transfer, wire, ach, trade, internal, card, crypto
- `timestamp` (str, optional): ISO 8601
- `transaction_id` (str, optional): For tracking

### explain_transaction

- `amount` (float, required)
- `transaction_type` (str, default: "wire_transfer")
- `timestamp` (str, optional)

### batch_check_compliance

- `transactions` (list): Each dict with `amount` (required), `transaction_type`, `timestamp`, `transaction_id`

### analyze_portfolio

- `transactions` (list): Same as batch_check_compliance

### ingest_transactions

- `transactions` (list): Same as batch_check_compliance

### list_incidents

- `status` (optional): open, resolved, escalated
- `severity` (optional): critical, high, medium, low
- `limit` (int, default: 20, max: 50)

---

## Return Shapes

### check_transaction_compliance

```json
{
  "transaction_id": "...",
  "decision": "approve" | "manual_review",
  "confidence": 85.0,
  "reasoning": "...",
  "anomaly_score": 0.1234,
  "risk_level": "low" | "medium" | "high",
  "risk_factors": [],
  "model_version": "...",
  "features": {},
  "regulation": "FINRA_4511"
}
```

---

## Rate Limits

- 60 calls per minute per tool (sliding window)
- Rate-limited responses return: `{"error": "Rate limit exceeded (60/min). Please slow down."}`

---

## Tracing & Metrics

- **OpenTelemetry:** Every tool call traced with `mcp.tool.<name>` span
- **Metrics:** `mcp_tool_calls_total`, `mcp_tool_duration_ms`
- **Usage stats:** GET `/mcp/stats` returns `total_calls`, `tools`, `avg_latency_ms`, `errors`, `recent`

---

## Resources

- `platform://metrics` — Current compliance metrics as JSON
- `platform://drift` — Model drift status as JSON
- `platform://regulations` — Supported regulatory frameworks (FINRA 4511, SEC 17a-4)

---

## Config

- **MCP_PUBLIC_URL** or **API_URL:** Used for `/mcp/tools` endpoint response (e.g. https://your-domain.com)
- **MCP_API_KEY:** Optional; when set, required for MCP protocol requests
