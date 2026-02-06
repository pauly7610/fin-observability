# OpenTelemetry Collector

Runs as a separate Railway service to receive traces and metrics from the backend via OTLP gRPC/HTTP.

## Architecture

```
Backend (FastAPI) ──OTLP gRPC:4317──> OTel Collector ──> Logging (stdout)
                                                     ──> Grafana Cloud / Honeycomb / Axiom (optional)
```

## Railway Setup

1. Deploy this directory as a separate service in the same Railway project
2. Set **Root Directory** to `otel-collector`
3. Railway auto-detects the Dockerfile
4. On the **backend** service, set:
   ```
   OTEL_EXPORTER_OTLP_ENDPOINT=<collector-service-name>.railway.internal:4317
   ```

## Forwarding to a Managed Backend

Edit `otel-collector-config.yaml` and uncomment the exporter you want:

### Grafana Cloud
Set these env vars on the collector service in Railway:
- `GRAFANA_CLOUD_API_KEY` — Base64-encoded `instanceId:apiKey`

### Honeycomb
- `HONEYCOMB_API_KEY` — Your Honeycomb team API key

### Axiom
- `AXIOM_API_TOKEN` — Your Axiom API token
- `AXIOM_DATASET` — Target dataset name

Then add the exporter name to the `exporters` list in each pipeline under `service.pipelines`.

## Local Development

```bash
docker build -t otel-collector .
docker run -p 4317:4317 -p 4318:4318 otel-collector
```
