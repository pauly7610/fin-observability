# Design Decisions & Tradeoffs

This document explains the *why* behind the architecture — the tradeoffs considered, alternatives rejected, and product thinking that shaped this platform.

---

## Why This Problem?

Financial AI systems have a trust gap. Models make decisions that affect real money and real compliance obligations, but the people accountable for those decisions — compliance officers, risk managers, regulators — often can't answer basic questions:

- Why did the model flag this transaction but not that one?
- Has the model's behavior changed since last quarter?
- When the analyst overrode the model's recommendation, was that logged?

Existing tools solve pieces of this (MLflow for model tracking, Datadog for APM, Splunk for audit logs), but none connect the full chain: **model inference → agent recommendation → human decision → audit trail**, all in one traceable pipeline.

That's the gap this platform fills.

---

## Architecture Decisions

### Why FastAPI + Next.js (not Django, not a monolith)?

**Decision:** Separate FastAPI backend + Next.js frontend in a monorepo.

**Tradeoff considered:** Django would give me an admin panel, ORM, and auth out of the box. But FastAPI's async-first design is better suited for a platform that needs to handle concurrent ML inference, LLM API calls, and real-time WebSocket updates without blocking. The type hints also generate OpenAPI docs automatically, which matters when the API surface is large (30+ endpoints).

Next.js was chosen over a SPA (Vite + React) because the App Router gives me server components, streaming, and a file-based routing convention that scales well as the dashboard grows. The frontend is a dashboard, not a marketing site — SSR isn't the point; the component model and developer experience are.

### Why an ML ensemble (not just Isolation Forest)?

**Decision:** Isolation Forest + PCA-Autoencoder, with ONNX Runtime for the autoencoder.

**Tradeoff considered:** A single Isolation Forest is fast and interpretable, but it only captures point anomalies — individual transactions that look unusual in isolation. Financial fraud often involves sequences (e.g., a series of small transactions that individually look normal but collectively represent structuring). The PCA-Autoencoder captures reconstruction error across feature dimensions, catching patterns that IF misses.

ONNX Runtime was chosen over raw PyTorch/TensorFlow inference because it's 3-5x faster for small models and has no GPU dependency — important for a Railway deployment where you're running on shared CPU instances.

**What I'd do differently at scale:** Replace the ensemble with a proper feature store + online inference pipeline (e.g., Feast + Seldon). The current in-process model works for thousands of transactions/day but wouldn't scale to millions.

### Why SHAP (not LIME, not attention weights)?

**Decision:** SHAP TreeExplainer for per-prediction feature importance.

**Tradeoff considered:** LIME is model-agnostic but slow (~100ms/prediction) and produces unstable explanations — run it twice on the same input and you can get different feature rankings. SHAP with TreeExplainer is exact for tree-based models (our Isolation Forest), runs in ~5ms, and produces consistent results.

The product reason matters more than the technical one: compliance officers need to trust the explanation. If the same transaction produces different explanations on different days, that trust breaks. SHAP's consistency is a feature, not just a nice-to-have.

### Why human-in-the-loop (not full automation)?

**Decision:** LLM agents recommend actions; humans approve them. No auto-execution by default.

**Tradeoff considered:** Full automation is faster. But in regulated financial services, the question isn't "can the AI do it?" — it's "who's accountable when it's wrong?" Auto-approving a transaction block that turns out to be a false positive has real consequences (customer impact, regulatory scrutiny).

The platform supports auto-approval for low-risk actions (configurable per role and action type), but defaults to human review. Every action — whether auto-approved or manually reviewed — records the full chain: agent input, output, reasoning, model version, and actor type. This isn't just good engineering; it's a regulatory requirement (SR 11-7, EU AI Act).

### Why OpenTelemetry (not Datadog, not custom logging)?

**Decision:** OpenTelemetry SDK with OTLP export to Grafana Cloud.

**Tradeoff considered:** Datadog is easier to set up and has better out-of-the-box dashboards. But it's vendor-locked and expensive at scale. OpenTelemetry is the industry standard — traces and metrics are portable across backends (Grafana, Jaeger, Honeycomb, Datadog itself).

More importantly, OTel lets me instrument the *decision pipeline*, not just the HTTP layer. I can create spans for "model inference," "SHAP computation," "agent reasoning," and "human approval" — then link them all under a single trace. That's the core value prop: you can follow a transaction from ingestion to final decision in one Grafana trace view.

**The dual-export design:** The backend sends traces directly to Grafana Cloud via OTLP/HTTP (for reliability), while the OTel Collector runs as a sidecar for host metrics and as a future fan-out point if we add more backends. This means traces still flow even if the collector goes down.

### Why drift detection triggers retraining (not a schedule)?

**Decision:** Retraining is triggered by drift detection (PSI + KS tests), not on a fixed schedule.

**Tradeoff considered:** Scheduled retraining (e.g., weekly) is simpler and predictable. But it's wasteful when the model is stable and dangerous when drift happens mid-week. PSI catches distribution shifts in the input features; KS tests catch changes in individual feature distributions. When either exceeds its threshold, retraining triggers automatically.

The thresholds are conservative (PSI > 0.25, KS p-value < 0.01) to avoid unnecessary retraining. A scheduled fallback still runs weekly as a safety net.

**What I'd do differently at scale:** Add a shadow scoring pipeline — retrained models score the same transactions as the production model, and promotion only happens when the challenger outperforms the champion on a holdout set. Right now, retraining replaces the model directly, which is acceptable for a single-instance deployment but not for production at scale.

### Why RBAC with four roles (not just admin/user)?

**Decision:** Four roles (admin, compliance, analyst, viewer) with 25 granular permissions.

**Tradeoff considered:** Two roles (admin/user) would be simpler. But the platform serves different personas with genuinely different needs:

- **Compliance officers** need to approve agent actions and resolve alerts, but shouldn't retrain models
- **Analysts** need to investigate anomalies and read audit logs, but shouldn't approve actions
- **Viewers** (e.g., auditors, regulators) need read-only access to everything, but shouldn't touch anything

The permission model is additive (each role gets a frozen set of permissions), not hierarchical. This avoids the "compliance can do everything analyst can do" assumption, which breaks when compliance shouldn't have access to model internals.

---

## What I'd Build Next

If this were a real product with a team:

1. **Model registry** — Version, promote, and roll back models with full lineage tracking. The current "retrain and replace" approach doesn't support A/B testing in production.
2. **Webhook integrations** — Push alerts to Slack, PagerDuty, or SIEM systems when anomalies or drift are detected. Currently everything lives in the dashboard.
3. **Multi-tenant isolation** — Row-level security or schema-per-tenant for serving multiple clients. The current single-tenant design is fine for a platform team but not for SaaS.
4. **Streaming ingestion** — Replace the REST API with Kafka/Redpanda for high-throughput transaction ingestion. The current sync API handles thousands/day but not millions.

---

## What I Intentionally Didn't Build

- **A custom ML framework** — scikit-learn + ONNX Runtime is boring and that's the point. The interesting problem is the observability and governance layer, not the model itself.
- **A custom UI component library** — shadcn/ui + TailwindCSS + Recharts. The frontend is a dashboard, not a design showcase. Ship fast, iterate on UX later.
- **Kubernetes** — Railway is simpler and sufficient for this scale. K8s would add operational complexity without solving a real problem at this stage.
- **Microservices** — A monolith with clean module boundaries (routers, services, ML, telemetry) is the right choice for a small team. Extract services when you have a scaling reason, not before.
