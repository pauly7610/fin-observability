# Fin Observability Frontend

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
