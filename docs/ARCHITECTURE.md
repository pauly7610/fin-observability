TECHNICAL.md

## Development Setup

pnpm install
pnpm dev # Starts all services

Key Scripts
pnpm build: Turbo-powered build

pnpm lint: Unified linting

pnpm generate: Type-safe API client gen

CI/CD Pipeline
Vercel for frontend

Dockerized FastAPI (Search Result 7)

Security scans with Trivy

### ARCHITECTURE.md

Data Flow

graph TD
A[Trader] --> B{Next.js}
B --> C[FastAPI]
C --> D[Agentic Core]
D --> E[(PostgreSQL)]
D --> F[SEC Audit Logs]
Key Decisions
Turborepo over Lerna (Search Result 4)

LangChain over custom agents

OpenTelemetry standard (Search Result 17)

### DESIGN.md

UI Principles
Real-time anomaly visualization

One-click compliance reports

Agent approval workflows

Compliance Features
SEC 17a-4 audit trails

FINRA 4511 data retention

Role-based access control
