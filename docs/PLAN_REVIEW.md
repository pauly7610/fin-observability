# Plan Review: Fix Auth, Tests, Consistency, and Documentation

This document reviews the implementation plan for correctness, missing items, and affected files before implementation.

---

## 1. Critical Pre-requisite: Clerk JWT Verification

**Issue:** The backend `decode_access_token` in [apps/backend/routers/auth.py](apps/backend/routers/auth.py) uses `JWT_SECRET_KEY` with HS256 and expects tokens from the backend's own `/auth/login` endpoint. Clerk issues tokens signed by Clerk's keys, not the backend's.

**Impact:** If we remove the api-client admin fallback (Phase 1.1) without adding Clerk JWT verification, signed-in users will receive 401 on all API calls because the backend cannot validate their Clerk tokens.

**Required fix before Phase 1.1:** Add Clerk JWT verification in the backend. Options:

- Use `@clerk/backend` or `pyjwt` with Clerk's JWKS URL to verify tokens
- Add `CLERK_JWKS_URL` or `CLERK_SECRET_KEY` to backend env
- In `get_current_user` (or a new dependency), when Bearer token is present, verify with Clerk first; if valid, look up or create user from Clerk claims

**Add to plan:** New Phase 0 or merge into Phase 1: "Implement Clerk JWT verification in backend security.py"

---

## 2. Connect Page Try It Live — Pre-existing Bugs

**Bug A — Wrong request payload:** The Connect page sends:

```json
{
  "transaction_id": "...",
  "amount": 25000,
  "type": "wire_transfer",
  "timestamp": "...",
  "source_account": "DEMO-001",
  "destination_account": "DEMO-002"
}
```

But `ComplianceMonitorTransaction` expects:

```json
{
  "id": "...",
  "amount": 25000,
  "type": "wire",
  "timestamp": "...",
  "counterparty": "...",
  "account": "..."
}
```

**Result:** The current Try It Live likely returns **422 Unprocessable Entity** (validation error).

**Bug B — Wrong response key for badge:** The Connect page checks `'decision' in tryResult` for the badge, but `/agent/compliance/monitor` returns `action` (not `decision`). The badge never displays.

**Plan correction:** Phase 2.1 should:

1. Fix the Connect page payload to match `ComplianceMonitorTransaction`: map `transaction_id` → `id`, `source_account` → `account`, `destination_account` → `counterparty`. Map `type`: schema accepts only `wire`, `ach`, `internal`; Connect dropdown uses `wire_transfer` — use `wire` when type is `wire_transfer`.
2. Fix the badge condition to use `tryResult.action || tryResult.decision`.

**Simpler alternative:** If we only fix the payload and badge, we can keep using `/agent/compliance/monitor` and skip adding a new endpoint. The response shape will differ from MCP (no `anomaly_score`, has `alternatives`, `audit_trail`) but the decision will be visible.

---

## 3. useMetrics and apiClient Base URL

**Clarification:** `useMetrics` uses `fetch('/api/metrics')` — a relative URL. With Next.js rewrites, the browser hits the Next.js server, which rewrites to the backend. The backend receives the request; auth headers may or may not be forwarded depending on fetch `credentials` and Next.js rewrite behavior.

**Plan correction:** When switching to `apiClient.get('/api/metrics')`, the request goes directly from the browser to `API_BASE_URL` (e.g. `http://localhost:8000`). This is a cross-origin request. Ensure:

- `NEXT_PUBLIC_API_URL` is set correctly for the environment
- CORS allows the frontend origin
- API calls use the same base URL as other authenticated requests

---

## 4. MCP Auth — Route Scope

**Clarification:** `/mcp/stats` and `/mcp/tools` are defined on the parent app, not the mounted MCP app. The mounted app handles the MCP protocol (e.g. Streamable HTTP).

**Plan correction:** MCP_API_KEY should apply only to requests that reach the **mounted** MCP app (the actual protocol). `/mcp/stats` and `/mcp/tools` are dashboard endpoints and should use normal auth (`get_current_user` or remain open for dashboard use).

**Middleware logic:**

- If `path in ["/mcp/stats", "/mcp/tools"]`: require `get_current_user` (or leave as-is for dashboard; if we add auth to /api/\*, add here too for consistency).
- If `path.startswith("/mcp")` and path not in ["/mcp/stats", "/mcp/tools"]: require MCP_API_KEY when env is set.

---

## 5. Anomaly Router — Schema and Type

**Verify:** [apps/backend/routers/anomaly.py](apps/backend/routers/anomaly.py) uses `txn_type` in some places. The MCP uses `transaction_type` with values like `wire_transfer`, `ach`. The anomaly router may use different parameter names. Confirm schema compatibility when adding auth.

---

## 6. /api/metrics Response Shape

**Verify:** Backend returns camelCase: `activeAlerts`, `complianceScore`, `complianceStatus`, etc. [apps/frontend/src/hooks/useMetrics.ts](apps/frontend/src/hooks/useMetrics.ts) `initialData` uses the same keys. No change needed when switching to apiClient.

---

## 7. 401 Redirect — Avoid Redirect Loops

**Plan addition:** When adding the 401 response interceptor, do not redirect if:

- Current path is `/sign-in`, `/sign-up`, or similar auth routes
- Request was a prefetch or background refetch (e.g. React Query)

Otherwise we may create redirect loops. Consider using `response.config.url` or a flag to skip redirect for certain requests.

---

## 8. DEMO_MODE Interaction

**Note:** When `DEMO_MODE=true`, `get_current_user` returns a demo viewer for unauthenticated requests. Removing the api-client fallback means:

- No token and no headers → backend receives nothing → `get_current_user` returns demo viewer (if DEMO_MODE) or 401 (if not).
- The admin fallback was the dangerous part; removing it is correct.
- Ensure DEMO_MODE is documented (e.g. in env.example) so deployers understand unauthenticated behavior.

---

## 9. Affected Files Summary

| File                                                    | Changes                                               |
| ------------------------------------------------------- | ----------------------------------------------------- |
| `apps/frontend/src/lib/api-client.ts`                   | Remove fallback; add 401 interceptor                  |
| `apps/backend/security.py`                              | Add Clerk JWT verification (new)                      |
| `apps/backend/routers/anomaly.py`                       | Add require_role to all 4 endpoints                   |
| `apps/backend/routers/compliance.py`                    | Add require_role to GET /compliance/logs              |
| `apps/backend/routers/agent.py`                         | Uncomment triage auth; add auth to GET /agent/actions |
| `apps/backend/main.py`                                  | Add auth to /api/\*; MCP middleware; dynamic MCP URL  |
| `apps/frontend/app/(dashboard)/connect/page.tsx`        | Fix Try It Live payload + badge (action/decision)     |
| `apps/frontend/src/hooks/useMetrics.ts`                 | Use apiClient instead of fetch                        |
| `apps/frontend/app/(dashboard)/explainability/page.tsx` | Use apiClient instead of fetch                        |
| `apps/backend/env.example`                              | Add MCP*API_KEY, MCP_PUBLIC_URL, CLERK*\*             |
| `apps/frontend/env.example`                             | Already has Clerk; add MCP_API_KEY note if needed     |

---

## 10. Recommended Implementation Order

1. **Phase 0 (new):** Implement Clerk JWT verification in backend — required before removing fallback.
2. **Phase 1.1:** Remove api-client fallback and add 401 redirect (with loop guards).
3. **Phase 1.3–1.6:** Add auth to backend endpoints.
4. **Phase 1.7:** MCP API key auth (exclude /mcp/stats and /mcp/tools from MCP key check).
5. **Phase 2.1:** Fix Connect Try It Live payload and badge (no new endpoint if payload fix is sufficient).
6. **Phase 2.2–2.3:** useMetrics and explainability apiClient migration.
7. **Phase 3+:** Config, tests, docs as in original plan.

---

## 11. Tests to Update After Auth Changes

- `test_compliance_monitor.py` — uses no auth; add `x-user-email`/`x-user-role` or obtain token.
- `test_integration.py` — uses `x-user-email`; should still work.
- `test_ops_metrics.py` — uses `x-user-email`; should still work.
- `test_webhooks.py` — uses `x-user-email`; should still work.

After removing the fallback, tests that rely on unauthenticated access will need to either use DEMO_MODE or provide valid auth headers/tokens.
