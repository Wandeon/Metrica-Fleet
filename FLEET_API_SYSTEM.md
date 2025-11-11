# Fleet Modular API System

## Objectives

- Deliver a modular, service-oriented API surface that aligns with fleet principles of atomic updates, safe defaults, and observability-first operations.
- Enable orchestration for staged deployments, guardrails (safe mode, rollbacks), and config-drift remediation defined in the fleet architecture.

## High-Level Architecture

```
┌───────────────────────────┐        ┌─────────────────────────┐
│ Device Agents (per role)  │  pull  │  Deployment Control API │
│ - Poll for updates        │◄──────►│  (Release service)      │
│ - Report status/metrics   │        └─────────────────────────┘
│ - Request overrides       │
└─────────▲───────┬─────────┘
          │       │ push telemetry
          │   ┌───▼──────────────────┐
          │   │ Fleet Telemetry API  │
          │   │ - Status ingest      │
          │   │ - Drift reports      │
          │   └───▲─────────┬────────┘
          │       │         │
   ┌──────┴──┐  ┌──┴────┐ ┌─┴──────────────────┐
   │ Ops UI  │  │ CI/CD │ │ Safe Mode Control  │
   │ & CLI   │  │Hooks  │ │ & Recovery API     │
   └─────────┘  └───────┘ └────────────────────┘
```

Each API module is independently deployable (e.g., separate containers behind a shared gateway) with shared identity, logging, and schema registry.

## Module Breakdown

### 1. Device Registry & Identity API

**Purpose:** Maintain canonical device metadata (role, segment, branch, hardware profile) that agents pull before every convergence run.

- **Key endpoints**
  - `GET /devices/{deviceId}` → role, segment, rollout eligibility, safe-mode state.
  - `PATCH /devices/{deviceId}` → authorized overrides (role swaps, maintenance mode).
  - `POST /devices/register` → bootstrap new device with signed config bundle.
- **Data contracts**
  - Include fields agents expect: `role`, `branch`, `segment`, `update_interval`, `event_stream_url`, `version_lock`, plus device metadata (serial, geolocation, owner).
- **Cross-module integration**
  - Publishes device changes to Deployment Control API for recalculating rollout sets.
  - Emits audit events for enterprise operations.

### 2. Deployment Control API

**Purpose:** Authoritatively manage staged releases, rollout percentages, and emergency rollbacks while respecting atomic update requirements.

- **Key endpoints**
  - `POST /releases` → declare new git commit + metadata (role, changelog, required migration).
  - `POST /releases/{id}/promote` with `targetSegment` (`canary`, `early`, `general`) or `rolloutPercentage`.
  - `POST /releases/{id}/rollback` → flip forced version / halt deployment.
  - `GET /releases/{id}/eligibility/{deviceId}` → agent-friendly eligibility snapshot.
- **Policies enforced**
  - Segment sequencing and waiting windows (enforce `canary → early → general`).
  - Deterministic hash-based gradual rollout when percentage mode is active.
  - Auto halt on failure-rate thresholds reported by Telemetry API.
- **Outputs**
  - Signed deployment manifest (commit hash, compose checksum, feature flags) served via CDN/Git mirror.
  - Real-time rollout events (`update_available`, `pause`, `rollback`) published to device event streams for immediate wakeups.

### 3. Fleet Telemetry & Drift API

**Purpose:** Provide ingestion for observability-first data: status, metrics hooks, drift reports, update results, and error summaries.

- **Key endpoints**
  - `POST /telemetry/status` → lightweight heartbeat payload (role, commit, last convergence, health enum).
  - `POST /telemetry/drift` → details from deep checks (checksum mismatches, permission issues).
  - `POST /telemetry/update-results` → success/failure of atomic swap with timing data.
  - `GET /telemetry/devices/{deviceId}` → consolidated timeline for dashboards.
- **Data sinks**
  - Writes summarized rows to Supabase/PostgreSQL schema envisioned in Phase 1.4.
  - Streams raw logs/metrics to Loki/Prometheus using append-only pipelines referenced in observability plan.
- **Realtime signals**
  - Emits WebSocket or SSE events for Ops UI to reflect rollout health in under 60 seconds.

### 4. Config & Artifact Service

**Purpose:** Serve versioned, validated artifacts (compose files, configs, checksum manifests) with strong caching and audit trails, backing the atomic replace pattern.

- **Key endpoints**
  - `GET /artifacts/{role}/{releaseId}/bundle` → tarball with compose, env templates, validation scripts.
  - `GET /artifacts/{role}/{releaseId}/checksums` → JSON for drift verification.
  - `POST /artifacts/validate` → CI hook that runs static validation before a release is publishable.
- **Versioning**
  - Immutable release IDs map to git commit hashes; older artifacts retained for rollbacks and forensic analysis.
- **Security**
  - Signed URLs with short TTLs to protect secrets management pipeline.

### 5. Safe Mode & Recovery API

**Purpose:** Manage device transitions into/out of the safe-mode stack, exposing minimal control plane operations when primary services fail.

- **Key endpoints**
  - `POST /recovery/{deviceId}/enter` → instruct agent to pivot to safe mode (also triggered automatically on agent failure).
  - `POST /recovery/{deviceId}/redeploy` → schedule re-attempt with chosen release once diagnostics pass.
  - `GET /recovery/{deviceId}` → fetch safe-mode diagnostics (logs, disk usage, last errors).
- **Integration**
  - Receives failure alerts from Telemetry API, automatically toggles per-device overrides to pause updates.
  - Coordinates with Deployment Control API to prevent further rollout while a device is quarantined.

### 6. Audit, Policy, and Governance API

**Purpose:** Provide enterprise-grade oversight—tracking configuration changes, agent actions, and compliance status.

- **Key endpoints**
  - `GET /audits?deviceId=...` → timeline of config edits, overrides, rollbacks.
  - `POST /policies` → define fleet-wide rules (e.g., minimum agent version, forced rollback windows).
  - `GET /compliance/report` → aggregated view for security teams (leverages monitoring events and drift reports).
- **Inputs**
  - Subscribes to event streams from all other modules to maintain immutable audit log, supporting the zero-tolerance-for-failure roadmap.

## Cross-Cutting Concerns

- **Authentication & Authorization:** Centralized OAuth/OIDC gateway with per-device certificates for agent calls; RBAC for human operators.
- **Schema Registry:** Versioned protobuf/JSON schemas so agents can gracefully roll between versions; backwards-compatible fields to avoid bricking devices mid-rollout.
- **Rate Limiting & Backpressure:** Align with exponential backoff and short-lived agent runs to prevent thundering herds when many devices poll simultaneously; event fanout keeps low-power devices mostly asleep.
- **Observability:** Every API exposes Prometheus metrics and structured logs to feed the monitoring stack defined in Phase 1.
- **Testing Hooks:** Synthetic chaos endpoints (e.g., `POST /test/fail-update`) to support the mandatory failure testing regime outlined in the critical roadmap.

## Implementation Sequence

1. Stand up Telemetry & Status ingest first to honor the observability-before-features principle; ensures dashboards exist before agent integration.
2. Build Deployment Control and Artifact services to provide rollout eligibility and versioned bundles before enabling writes from agents.
3. Ship Safe Mode API to guarantee recovery path prior to full rollout.
4. Layer in Audit/Policy capabilities once core flows are stable, enabling compliance automation.
