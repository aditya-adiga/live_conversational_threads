# Instrumentation, Metrics, Storage, and Testing Roadmap

**Last updated:** 2025-11-11  
**Status:** Draft for implementation planning

This roadmap stitches together the observability, data storage, and quality guarantees required to safely launch the Week 11–14 features (Simulacra Levels, Cognitive Biases, Implicit Frames, and Rhetorical Profiles). It translates existing Tier 1/Tier 2 specs into actionable workstreams that ensure we can measure cost, latency, accuracy, and user impact across the stack.

---

## Guiding Principles

- **Every AI action is measurable**: Token usage, latency, and outcomes for LLM calls must be captured and queryable within minutes.  
- **Product analytics stay explainable**: Speaker metrics, bias detections, and frames share a single source of truth with reproducible calculations.  
- **Storage tiers mirror retention value**: Hot Postgres metadata, warm Parquet aggregates, and cold GCS archives with explicit lifecycle policies.  
- **Testing protects conversations**: Unit and integration tests cover data contracts so instrumentation never corrupts transcripts or analytical outputs.

---

## Current Gaps

1. **Instrumentation**: `middleware/instrumentation.py` is sketched but not wired into FastAPI routes or LLM clients. Front-end telemetry is missing.  
2. **Metrics**: No canonical catalog for LLM cost/performance, product KPIs (bandwidth, Simulacra accuracy), or alert thresholds.  
3. **Storage**: GCS usage for transcripts is manual; there is no warm tier for analytical aggregates or retention automation.  
4. **Testing**: No dedicated tests for telemetry decorators, metrics calculators, or storage lifecycles; CI does not enforce coverage gates for new analytical code.

---

## Workstreams at a Glance

| Workstream | Scope | Primary Outputs | Lead Function |
|------------|-------|-----------------|---------------|
| Telemetry Instrumentation | Backend + frontend event collection, LLM call tracing | OpenTelemetry collectors, API call log table, privacy filters | Platform |
| Metrics & Analytics | KPI definitions, dashboards, anomaly alerts | Metrics catalog, dbt/DuckDB models, Grafana boards | Analytics |
| Storage & Retention | Hot/warm/cold tiers, archival automation | Postgres schemas, Parquet export jobs, GCS lifecycle rules | Infra |
| Testing & Quality Gates | Unit/integration tests, CI wiring, synthetic data | Pytest/Vitest suites, contract tests, coverage reporting | QA |

---

## Phase Plan

### Phase 0 – Foundations (Week 10 carryover)
- Ship `track_api_call` decorator and persist to `api_calls_log`.  
- Stand up OpenTelemetry Collector (OTLP HTTP) for FastAPI + React dev builds.  
- Document PII handling + sampling rules.

### Phase 1 – Instrumentation Baseline (Week 11)
- Instrument all Week 11 endpoints (Simulacra detection, bias pre-filter, implicit frame extractor) with tracing, structured logs, and cost tracking.  
- Add front-end event bus to capture node detail interactions (expand/collapse, severity overrides).  
- Deliver dark-mode Grafana board for LLM latency, cost, error rate.

### Phase 2 – Metrics + Storage Enablement (Week 12)
- Publish metrics catalog (definitions, owners, alert thresholds).  
- Build nightly job that materializes product metrics into Parquet/DuckDB for Analytics View dashboards.  
- Implement warm tier retention (30-day Postgres, 180-day Parquet, long-term GCS).  
- Hook severity feedback loop (user correction object) into telemetry stream.

### Phase 3 – Testing & Hardening (Week 13)
- Add pytest suites for instrumentation middleware, cost calculators, and storage retention helpers.  
- Add Vitest/Playwright flows validating UI telemetry payloads.  
- Introduce CI gates: schema contract tests + minimum coverage (80% for telemetry modules).  
- Run load test + chaos rehearsal for OTLP pipeline.

### Phase 4 – Continuous Improvement (Week 14+)
- Layer speaker-level analytics + steelmanning scoring metrics.  
- Automate anomaly detection (drift in Simulacra classifications) and incident runbooks.  
- Expand archival tooling (hash-based dedupe, cold restore automation).

---

## Detailed Plans

### 1. Telemetry & Instrumentation

#### Backend (FastAPI + workers)
- Adopt `opentelemetry-sdk` with FastAPI instrumentation + `AsyncPGInstrumentor` for database spans.  
- Wrap all LLM calls (`call_llm`, AssemblyAI streaming, Perplexity) with `@track_api_call`. Persist latency/tokens/cost to `api_calls_log`.  
- Standardize structured logging via `structlog`, ensuring request IDs propagate to background tasks.  
- Add circuit-breaker metrics (retry counts, provider fallback usage) for bias/frame detectors.  
- Emit domain events (`simulacra.classified`, `bias.flagged`, `frame.detected`) to a lightweight Redis or in-process queue before landing in Postgres `telemetry_events`.

#### Frontend (React / Vite)
- Implement a thin telemetry client that batches events (`detail_panel.view`, `bias.override`, `feedback.submit`) and ships via `navigator.sendBeacon`.  
- Decorate expensive UI actions (canvas zoom, node expansion) with `performance.mark` + `performance.measure` and forward to OTLP over HTTPS.  
- Respect privacy: never ship transcript text without hashing; include node IDs + redacted metadata only.

#### Governance
- Maintain a YAML registry (`telemetry/metrics.yml`) with event names, payload schema, and responsible teams. Required for schema validation in CI.  
- Sampling rules: 100% capture in staging; production defaults to 20% for UI events, 100% for LLM cost telemetry, burstable to 100% during incidents.  
- Secrets: OTLP exporter configured via `OTEL_EXPORTER_OTLP_HEADERS` + `.env` placeholders already documented in README.

### 2. Metrics Strategy

#### Catalog Highlights
- **System**: API latency (p95/p99), worker queue depth, LLM success %, token-per-node, cost-per-conversation.  
- **Product**: Simulacra level distribution, bias flag rate per conversation, implicit frame coverage, steelmanning score, user feedback agreement rate.  
- **Quality**: Precision/recall from adjudicated datasets, drift metrics vs. golden sets, ratio of manual overrides per 100 nodes.

#### Implementation
- Create dbt (or DuckDB SQL) models that aggregate `telemetry_events` + `api_calls_log` nightly; store results both in Postgres materialized views for dashboards and Parquet files in `analytics/` GCS folder.  
- Publish Grafana dashboards: `LLM Cost`, `Product Quality`, `User Feedback Loop`. Each dashboard links to runbooks.  
- Alerts: hook Grafana → Slack for thresholds (e.g., `bias.flag_rate > 35%`, `llm_error_rate > 2%`).

### 3. Storage & Retention

| Tier | Storage | Data Types | Retention | Notes |
|------|---------|------------|-----------|-------|
| Hot | Postgres (`conversations`, `api_calls_log`, `telemetry_events`) | Metadata, node graph, fresh telemetry | 30 days rolling | Indexed for UI + APIs |
| Warm | Parquet/DuckDB in `gs://<bucket>/analytics/` | Aggregated metrics, denormalized speaker stats | 6 months | Versioned, supports ad-hoc queries |
| Cold | GCS `archives/` | Raw transcripts, audio, model responses | 2 years (configurable) | Lifecycle rules move to Archive class after 12 months |

Additional actions:
- Implement nightly export job (FastAPI task or Cloud Run job) that snapshots Postgres telemetry into Parquet partitions by `event_date`.  
- Encrypt everything at rest (GCS CMEK) and in transit (TLS).  
- Add bloom-filter index for quick GDPR deletion requests.  
- Define `storage_manifest` JSON per conversation summarizing file handles, retention class, checksum.

### 4. Testing & Quality Gates

#### Backend
- `tests/test_instrumentation.py`: simulate successful + failing LLM calls, assert DB log entries and OTLP spans.  
- `tests/test_metrics.py`: feed fixtures of telemetry events; validate aggregated metrics + severity calculations.  
- `tests/test_storage_policy.py`: ensure retention helper schedules correct hot/warm/cold transitions.

#### Frontend
- `vitest` for telemetry client (payload schema, batching logic).  
- `playwright` smoke that walks through node detail interactions and asserts telemetry hits via mock OTLP endpoint.  
- Snapshot tests for metrics visualization colors (Simulacra levels, severity badges).

#### CI / Tooling
- Enforce schema validation using `datamodel-codegen` or JSON Schema for telemetry payloads.  
- Minimum coverage: 80% for `middleware/instrumentation.py`, 75% for metrics calculators, 70% for storage helpers.  
- Add `make telemetry-check` to run schema lint + static analysis.  
- Add canary job that replays last 1k events against staging aggregator weekly.

---

## Implementation Checklist (Living)

- [ ] Land OTLP exporter configs + collector manifests.  
- [ ] Create `api_calls_log`, `telemetry_events`, and `storage_manifests` tables.  
- [ ] Wire `track_api_call` decorator into every LLM helper, including streaming transcripts.  
- [ ] Build React telemetry client + consent UI.  
- [ ] Publish metrics catalog + Grafana boards.  
- [ ] Configure GCS lifecycle + checksum validator.  
- [ ] Add pytest/vitest coverage + CI gates.

---

## Dependencies & Risks

- **AssemblyAI / Anthropic rate limits**: Need synthetic load harness to avoid noisy telemetry during replay.  
- **Storage costs**: Parquet snapshots can explode without partition pruning; enforce weekly compaction.  
- **Privacy**: Telemetry must exclude raw transcript text; redaction validators run in CI.  
- **Team Bandwidth**: Instrumentation requires coordination across platform, analytics, and UX—assign DRI per workstream early.

---

## Open Questions

1. Do we centralize event ingestion via Kafka/Redpanda, or is Postgres + OTLP sufficient for v1?  
2. Which visualization stack is preferred (Grafana vs. Lightdash) for Analytics View alignment?  
3. How aggressively should we sample UI telemetry once data volume grows beyond 10M events/month?  
4. Do we need SOC2-style immutable logs for enterprise prospects?

> Update this roadmap at the end of each sprint; treat unchecked items as blockers for the Week 12 production release.

