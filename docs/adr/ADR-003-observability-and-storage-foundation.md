# ADR-003: Observability, Metrics, and Storage Baseline

**Status**: Proposed  
**Date**: 2025-11-11  
**Deciders**: Platform + Analytics Working Group  
**Technical Story**: Deliver Week 11–14 AI features with measurable cost, accuracy, and retention guarantees

## Context and Problem Statement

Tier 2 has sketches for `middleware/instrumentation.py` and cost tracking, but the production stack still runs without:

1. End-to-end tracing of LLM calls, user interactions, or background jobs.  
2. A shared metrics catalog covering system health, AI quality, and product KPIs.  
3. Storage tiers that distinguish between hot metadata, analytical aggregates, and long-lived transcripts/audio.  
4. Regression tests that ensure telemetry changes do not corrupt data models.

Week 11–14 introduces Simulacra levels, bias detection, implicit frames, and rhetorical profiles—features that require accurate metrics (e.g., level distribution, override rates) and compliance-ready retention. We need a single decision on which observability stack, data stores, and testing guarantees to adopt.

## Decision Drivers

1. **Unified Tracing**: Backend, workers, and frontend must emit spans/events we can correlate per conversation.  
2. **Cost Transparency**: Track LLM usage (tokens, USD) to prevent runaway invoices.  
3. **Analytics Consistency**: Product dashboards must rely on reproducible aggregates.  
4. **Compliance & Privacy**: PII must stay encrypted, redacted from telemetry payloads, and deletable.  
5. **Developer Ergonomics**: Minimal ceremony to instrument new endpoints; testing must be fast.

## Considered Options

### Option A: Ad-hoc Logging + Postgres Only
- Decorators log API metadata into Postgres tables; no tracing or collectors.

**Pros**  
- Minimal dependencies; easy to implement.  
- All data stays inside existing DB.

**Cons**  
- No distributed traces or correlation IDs.  
- Hard to sample/high-volume UI events.  
- Postgres bloats quickly; no retention tiers.  
- Poor tooling for dashboards/alerts.

### Option B: Managed SaaS (Datadog/New Relic) + GCS Snapshots
- Send traces/metrics to managed observability SaaS; periodically dump DB snapshots to GCS.

**Pros**  
- Best-in-class dashboards and alerting.  
- Less infra to maintain.

**Cons**  
- Vendor lock-in and higher cost.  
- Harder to keep self-hosted/offline story (product vision stresses open source + self-host).  
- SaaS cannot store user transcripts due to privacy constraints.

### Option C: OpenTelemetry + Postgres Hot Tier + Parquet Warm Tier (Chosen)
- Instrument backend/frontend with OpenTelemetry (OTLP HTTP exporter).  
- Store raw telemetry + metadata in Postgres; nightly export aggregates to Parquet/DuckDB on GCS.  
- Cold storage stays in GCS with lifecycle policies; Grafana/Prometheus power dashboards.

**Pros**  
- Open standard; can self-host or plug into any backend.  
- Works offline/on-prem; aligns with open-source posture.  
- Clear hot/warm/cold story with lifecycle automation.  
- Easy to test locally by pointing OTLP to file or collector.  
- Grafana/Prom stack already familiar to team.

**Cons**  
- Requires operating OpenTelemetry Collector + Grafana stack.  
- Need to enforce sampling + privacy filters ourselves.  
- Slightly higher initial setup effort vs. ad-hoc logging.

## Decision Outcome

**Adopt Option C (OpenTelemetry + tiered storage).**

### Architecture Changes

1. **Telemetry Collector**  
   - Deploy OTLP collector alongside backend; exports traces/metrics to Prometheus (metrics) and Loki/Tempo (logs/traces).  
   - Backend uses `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, and custom span attributes for conversation + node IDs.  
   - Frontend batches events through a lightweight OTLP HTTP client with PII redaction.

2. **Data Stores**  
   - **Hot**: Postgres tables `api_calls_log`, `telemetry_events`, `storage_manifests`.  
   - **Warm**: Nightly job writes Parquet files partitioned by `event_date` + `event_type` to `gs://<bucket>/analytics/`, optionally queried via DuckDB/dbt.  
   - **Cold**: GCS buckets with lifecycle policies (`standard` → `nearline` → `archive`) for transcripts, audio, raw LLM responses.

3. **Metrics Catalog + Dashboards**  
   - YAML registry enumerates each KPI (definition, owner, alert thresholds) checked into repo.  
   - Grafana dashboards: `LLM Cost`, `Product Quality`, `User Feedback`. Alert rules route to Slack/Email.

4. **Testing & Contracts**  
   - Pytest fixtures spin up OTLP test collector to assert emitted spans/logs.  
   - JSON Schema validates telemetry payloads (CI).  
   - Snapshot-based tests verify Parquet exports match schema + partitioning rules.

### Security & Privacy

- OTLP exporters scrub transcript text; only node IDs/hash references travel through telemetry.  
- GCS buckets enforce CMEK + IAM roles (principle of least privilege).  
- Retention helper enforces GDPR delete by referencing `storage_manifest`.

## Consequences

**Positive**
- Consistent instrumentation for new AI features; easier incident triage.  
- Ability to compute ROI for LLM pipelines (cost per conversation).  
- Analytics View (speaker profiles, steelmanning score) backed by authoritative data.  
- Portable architecture for on-prem customers.

**Negative**
- Additional services to run (collector, Grafana, Prometheus).  
- Need team training on OpenTelemetry semantics and sampling.  
- More upfront engineering to wire decorators/tests.

## Follow-up Actions

1. Build collector manifests + Terraform (or Docker Compose) examples.  
2. Create Postgres migrations for `api_calls_log`, `telemetry_events`, `storage_manifests`.  
3. Implement telemetry client libraries (Python + React).  
4. Land Grafana dashboards and document alert playbooks.  
5. Add roadmap cross-link: `docs/ROADMAP_INSTRUMENTATION_METRICS.md`.

> Refer to the roadmap for sprint-by-sprint ownership. This ADR locks the stack choice so teams can proceed without re-litigating the foundation.

