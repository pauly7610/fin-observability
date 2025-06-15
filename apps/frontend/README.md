# Fin Observability Frontend

## Overview

This frontend powers the trading operations AI automation platform for the Fin Observability system. It provides dashboards and workflows for trading incident management, agentic triage, remediation, approvals, and trading desk automation. Compliance and audit trail features are fully supported but are not the primary focus.

### Key Features

- **Trading Ops Dashboard:** Real-time incident monitoring, triage, and remediation for trading desks.
- **Agentic Workflows:** Surfaces AI-driven recommendations, explainability, and escalation actions.
- **Approval Flows:** Multi-party, role-based approvals for sensitive trading operations.
- **Audit & Compliance:** Full audit trail for every action, with detailed history and SIEM integration.
- **Modern UI/UX:** Built with React/Next.js, Tailwind CSS, and modular, accessible components.

## Audit Trail Component

### Overview

The `AuditTrail` React component provides a detailed, visually polished audit/history view for all major resource detail pages (Incidents, Compliance Logs, Users, Agentic Workflows). It enhances operational transparency and compliance by showing a chronological list of all actions taken on a resource.

### Features

- **Chronological log:** Lists all audit actions for the resource (create, update, delete, assign, escalate, comment, resolve, login, etc.).
- **Icons & Color Coding:** Each action type is displayed with a distinct icon and color for quick visual recognition.
- **Expandable Details:** Users can expand/collapse each log entry to view full details, keeping the UI clean and focused.
- **Accessibility:** Expand/collapse controls are keyboard accessible and use ARIA attributes.
- **Responsive & Themed:** Uses Tailwind CSS and theme variables for a modern, consistent look.

### Usage

The component is automatically included at the bottom of:

- `pages/incidents/[id].tsx`
- `pages/compliance/[id].tsx`
- `pages/users/[id].tsx`
- `pages/agentic/[id].tsx`

It fetches audit data from `/audit/{resource}/{resourceId}` using the shared `apiRequest` utility.

#### Example (already in codebase):

```tsx
<AuditTrail resource="incidents" resourceId={id as string} />
```

### Customization

- **Icons and colors:** Easily extend `actionIcons` and `actionColors` in `components/layout/AuditTrail.tsx` to support new action types.
- **Expandable details:** Details are hidden by default and can be shown with a button for each entry.

### Backend Requirements

- The backend must expose an endpoint `/audit/{resource}/{resourceId}` returning an array of audit log entries with fields: `id`, `timestamp`, `action`, `details`, `user`, `category`.

### Example Entry

```json
{
  "id": "log-123",
  "timestamp": "2025-06-09T21:15:00Z",
  "action": "Assigned Incident",
  "details": "Assigned to user alice.",
  "user": "alice",
  "category": "assignment"
}
```

### UI/UX Details

- **Icon and color** reflect action type (e.g., 🟢 for create, 📝 for update, 🗑️ for delete, etc.).
- **Timestamp** is shown in local time.
- **User** and **category** are always visible.
- **Details** are expandable/collapsible for each entry.

### Accessibility

- Expand/collapse uses `aria-expanded` and `aria-controls` for screen reader support.

### Location

- `src/components/layout/AuditTrail.tsx`

---

## Recent Improvements

- Added toast notifications for all major actions (exports, users, incidents, compliance, etc.).
- Added and polished the AuditTrail component for operational transparency.
- All new features are fully integrated and visually consistent.

---

For further customization or to add new resource types, extend the `AuditTrail` component and update the backend API accordingly.

## Recent Integration & Real-Time Features (2024-06)

### Major Updates

- **Hooks & API Integration:** All hooks (useAIAgentActivity, useCompliance, useAlerts, useMetrics, useSystems) updated to match backend endpoints and data shapes.
- **WebSocket Support:** Real-time updates for incidents and compliance via `/ws/incidents` and `/ws/compliance` endpoints.
- **Proxy/Rewrite:** Next.js now proxies `/api/*` requests to the backend for seamless local development. See `next.config.js`.
- **Error Handling:** Improved error boundaries and null checks for robust UI.
- **Test Data:** Backend returns mock data for systems, incidents, and compliance if the database is empty.
- **OpenTelemetry Tracing:** To enable backend tracing, run:
  ```sh
  docker run --name otel-collector -p 4317:4317 -p 4318:4318 -p 55681:55681 otel/opentelemetry-collector:latest
  ```

### Troubleshooting

- **API 404s:** Ensure the rewrite rule is present and restart the dev server after changes.
- **WebSocket Errors:** Backend endpoints must call `await websocket.accept()` and have no permission checks for local testing.
- **.map Errors:** The backend now returns `{ systems: [...] }` for `/api/systems`. Use `data.systems.map(...)` in the frontend.
- **Tracing Exporter Errors:** If you see `StatusCode.UNAVAILABLE`, ensure the collector is running as above.
- **DeprecationWarnings:** If you see `util._extend` warnings, update dependencies with `npm update`.
- **Vue Source Map 404s:** These are likely from browser extensions and can be ignored unless you are developing Vue components.
