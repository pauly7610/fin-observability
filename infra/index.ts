/**
 * Pulumi Infrastructure as Code for Financial Observability Platform
 *
 * Defines the Railway infrastructure:
 * - Backend service (FastAPI)
 * - PostgreSQL database
 * - Redis cache
 * - OTel Collector sidecar
 *
 * Usage:
 *   cd infra
 *   npm install
 *   pulumi up
 *
 * Prerequisites:
 *   - Pulumi CLI installed
 *   - Railway API token: `pulumi config set railway:token <token> --secret`
 */
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();

// Railway project configuration
const projectName = "fin-observability";
const railwayProjectId = config.get("railwayProjectId") || "fa95a33a-95b3-42ba-a4cd-a3cba535cbc6";

// Environment variables
const envVars = {
  // Database — set by Railway Postgres plugin, referenced here for documentation
  DATABASE_URL: config.getSecret("databaseUrl") || pulumi.interpolate`\${{Postgres.DATABASE_URL}}`,

  // Auth
  JWT_SECRET_KEY: config.requireSecret("jwtSecretKey"),
  JWT_EXPIRE_MINUTES: config.get("jwtExpireMinutes") || "60",

  // CORS
  CORS_ORIGINS: config.get("corsOrigins") || "*",

  // OTel
  OTEL_EXPORTER_OTLP_ENDPOINT: "ravishing-prosperity.railway.internal:4317",

  // LLM (optional)
  OPENAI_API_KEY: config.getSecret("openaiApiKey") || "",

  // Drift detection
  DRIFT_CHECK_HOURS: config.get("driftCheckHours") || "6",

  // Retraining schedule (fallback if drift detection is disabled)
  RETRAIN_SCHEDULE_HOURS: config.get("retrainScheduleHours") || "168",
};

// OTel Collector environment variables
const otelCollectorEnvVars = {
  GRAFANA_CLOUD_API_KEY: config.getSecret("grafanaCloudApiKey") || "",
};

// Export configuration for reference
export const project = {
  name: projectName,
  id: railwayProjectId,
  services: {
    backend: {
      rootDirectory: "/",
      dockerfile: "Dockerfile",
      startCommand: "sh -c 'uvicorn apps.backend.main:app --host 0.0.0.0 --port ${PORT:-8000}'",
      healthcheckPath: "/health",
      envVars: Object.keys(envVars),
    },
    otelCollector: {
      rootDirectory: "otel-collector",
      dockerfile: "otel-collector/Dockerfile",
      envVars: Object.keys(otelCollectorEnvVars),
    },
    postgres: {
      plugin: "postgresql",
      version: "16",
    },
  },
};

/**
 * NOTE: Railway does not yet have an official Pulumi provider.
 * This file serves as Infrastructure-as-Code documentation and
 * can be extended with the Railway API when a provider becomes available.
 *
 * For now, use this as a reference for:
 * 1. What services exist and their configuration
 * 2. What environment variables are required
 * 3. How services are connected
 *
 * To manage Railway infrastructure programmatically, use the Railway CLI:
 *   railway login
 *   railway link <project-id>
 *   railway variables set KEY=VALUE
 */
