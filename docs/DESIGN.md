# DESIGN.md

## Design Vision

The Financial AI Observability Platform blends the real-time, data-rich feel of classic trading dashboards with the intuitive, workflow-centric experience of modern agentic platforms. The result is a system that empowers trading ops and compliance teams to monitor, act, and collaborate with AI agents—seamlessly and confidently.

---

## Key Design Principles

1. **Real-Time, Modular Dashboard**
   - Persistent panels for live metrics, alerts, and compliance status.
   - Dense tables and charts in a grid layout, optimized for ultrawide monitors.
   - Dark mode by default, with high-contrast elements for clarity.

2. **Agentic Command & ChatOps**
   - Always-available command bar (bottom or via hotkey) for natural language and slash commands.
   - Conversational agent panel for step-by-step workflows, agent suggestions, and approvals.

3. **Workflow & Task Sidebar**
   - Sidebar or overlay listing ongoing, pending, and completed agentic tasks.
   - Each task shows status, owner (agent/human), and next action.
   - Click into tasks for full audit trail and agent reasoning.

4. **Actionable Notifications & Suggestions**
   - Inline agentic prompts (“Agent recommends restart—approve?”) with one-click actions.
   - Color-coded notifications for severity and urgency.

5. **Compliance & Audit Transparency**
   - Compliance badges always visible (SEC 17a-4, FINRA).
   - Filterable audit log panel, exportable as CSV/PDF.
   - “Download Compliance Report” and “View Agent Actions” always one click away.

6. **Personalization & Shortcuts**
   - Customizable dashboard layouts (drag-and-drop panels, save presets).
   - Keyboard shortcuts for power users.
   - User profile with role-based views (Trader Ops, Compliance Officer, Admin).

---

## Visual Layout

```
+---------------------------------------------------------------+
|   Top Bar: [System Status] [Search/Command] [User]           |
+-------------------+-----------------------------+------------+
| Navigation        | Main Dashboard              | Task/Agent |
| [Dashboard]       | [Live Metrics Panel]        | [Workflow  |
| [Alerts]          | [Anomaly Chart]             | Sidebar:   |
| [Compliance]      | [Alert Table]               | - Ongoing  |
| [Reports]         | [Compliance Badges]         |   Tasks    |
|                   | [Agentic Chat Panel]        | - Pending  |
|                   |                             |   Approval |
+-------------------+-----------------------------+------------+
| Command Bar: > /investigate latency FX                            |
+---------------------------------------------------------------+
| Audit Log Panel (Collapsible): [Timeline] [Filter] [Export]   |
+---------------------------------------------------------------+
```

---

## UI Component Guide

- **Live Metrics Panel:** Real-time line/bar charts with threshold overlays.
- **Alert Table:** Sortable, filterable table (Time, Severity, System, Status, Action).
- **Compliance Badges:** Pill-shaped, color-coded, always visible.
- **Agentic Chat Panel:** Conversational interface for agent workflows, suggestions, and approvals.
- **Workflow Sidebar:** List of agentic tasks with status, owner, and quick actions.
- **Command Bar:** Natural language and slash command input, with autocomplete and history.
- **Audit Log Panel:** Chronological, filterable, exportable; shows both human and agent actions.

---

## Color & Typography

- **Primary background:** #181A1B (dark gray)
- **Panel background:** #232526
- **Accent colors:**
  - Success: #1DB954
  - Warning: #FFD600
  - Error: #FF1744
  - Info: #2D7DFF
- **Text:** #FAFAFA (main), #B0BEC5 (secondary)
- **Font:** Inter, Roboto Mono (for numbers/tables)

---

## Familiarity Touchpoints

- Dense, grid-based layout echoes Bloomberg/Geneos.
- Command bar and agentic chat inspired by Factory.app and Slack.
- Task sidebar and notifications for workflow transparency.
- Compliance and audit always visible, never hidden in menus.
- Industry terms and abbreviations (“LCR,” “FX,” “Order Router”) used throughout.

---

## End-User Workflow Example

1. **User logs in:** Sees live system health, open incidents, agentic tasks, and compliance status.
2. **Alert fires:** Pops up in alert table and as a notification; agentic chat suggests a root cause and recommended action.
3. **User issues command:** Types “/restart order router” in command bar; agent confirms, logs action, and updates task sidebar.
4. **Agentic workflow:** Agent handles multi-step triage, asks for human approval before any risky action, and logs everything.
5. **Compliance officer:** Downloads audit trail and compliance report in one click from the dashboard.

---

## MCP Integration

- **Purpose:** Expose compliance monitoring, anomaly detection, explainability, and metrics as MCP tools so any AI agent (Claude, Cursor, Windsurf) can connect.
- **Tool catalog:** 9 tools including `check_transaction_compliance`, `explain_transaction`, `batch_check_compliance`, `analyze_portfolio`, `ingest_transactions`, `get_compliance_metrics`, `list_incidents`, `get_drift_status`, `get_model_leaderboard`.
- **Auth:** When `MCP_API_KEY` env var is set, AI clients must pass it via `X-MCP-API-Key` header or `Authorization: Bearer <key>`. Dashboard endpoints `/mcp/stats` and `/mcp/tools` use normal user auth.
- **Connect page:** Copy config for Windsurf, Claude, or Cursor; Try It Live uses `POST /api/compliance/check` for MCP-equivalent response.

---

## API Auth

- **Flow:** Frontend uses Clerk for sign-in; `AuthTokenProvider` passes `getToken()` to `api-client`. Backend validates JWT or header auth; when no token, returns 401 or demo viewer (when `DEMO_MODE=true`).
- **Fallback:** No admin fallback. Unauthenticated requests receive 401; frontend redirects to `/sign-in` on 401.
- **Headers:** `Authorization: Bearer <token>` or `x-user-email` + `x-user-role` (for dev/testing).

---

## Webhook & Ingestion

- **Webhook:** POST transactions to `/webhooks/transactions`; each is scored and stored. Auth via `X-Webhook-Key`.
- **MCP:** `ingest_transactions` tool pushes up to 10,000 transactions for scoring + storage.
- **Kafka:** When `KAFKA_BROKERS` is set, consumer runs in-app; events (orders, executions, trades) create incidents.
- **Pull:** Scheduled pull sources fetch from external APIs; configurable via `/webhooks/pull/sources`.

---

## Accessibility

- High-contrast colors for all critical information.
- Keyboard navigation and shortcuts for all major actions.
- Screen-reader support for alerts, agentic chat, and compliance info.

---

[See PRD.md for detailed feature demonstrations and business value articulation.]
