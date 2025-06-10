Financial AI Observability Platform
Overview
This monorepo contains the full-stack implementation of a Financial AI Observability platform designed to provide real-time anomaly detection, compliance monitoring, and agentic AI-driven automation for financial services clients.

Features
Real-time anomaly detection using Isolation Forest and KNN models.

Compliance monitoring with SEC 17a-4 and FINRA 4511 audit trails.

Agentic AI capabilities with LangChain for incident triage and remediation.

OpenTelemetry instrumentation compatible with ITRS Geneos platform.

Kafka streaming stubs for event ingestion.

Next.js frontend with real-time dashboard and compliance badges.

Approval Workflow & Compliance
-----------------------------
Sensitive actions and exports are protected by a robust approval workflow.
All major backend actions (agentic triage, remediation, compliance exports,
user data exports, etc.) require explicit approval from privileged users
(`admin`, `compliance`, or `analyst` roles) before execution.

- Approval requests are surfaced in a dedicated frontend dashboard, in resource
  detail pages, and in the sidebar for quick access.
- Only authorized users can approve/reject, with clear UI feedback and audit
  logging.
- All approval actions and decisions are fully audit-logged and surfaced in the
  audit trail for compliance and transparency.
- Batch approval/rejection is supported in the UI for power users.
- The workflow is designed for extensibility (multi-step, multi-role, etc.).

Monorepo Structure
text
fin-ai-observability/
├── apps/
│ ├── frontend/ # Next.js 14.2.1 (App Router)
│ └── backend/ # FastAPI 0.111.0
├── packages/
│ ├── agentic-core/ # LangChain 0.2.0, OpenAI 1.25.0
│ ├── shared-types/ # TypeScript 5.5.x
│ └── telemetry/ # OpenTelemetry Python 1.25.0, JS 1.20.0
├── docs/
│ ├── ARCHITECTURE.md
│ ├── TECHNICAL.md
│ ├── DESIGN.md
│ └── AGENTIC.md
└── turbo.json # Turborepo 1.15.0
Getting Started
Prerequisites
Node.js 20.x

Python 3.12.x

PostgreSQL 15.x

Installation
bash
pnpm install
Running the Development Environment
bash
pnpm dev
Testing
Backend tests with pytest

Frontend tests with Jest and React Testing Library

Contributing
Please see CONTRIBUTING.md for guidelines.

License
MIT
