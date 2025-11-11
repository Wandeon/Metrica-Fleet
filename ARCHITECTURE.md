# Metrica Fleet - Detailed Architecture

This document provides in-depth technical details on the Metrica Fleet system design, covering advanced scenarios, edge cases, and production considerations.

## Table of Contents

1. [Deployment Strategies](#deployment-strategies)
2. [Config Drift Detection](#config-drift-detection)
3. [Update Collision Handling](#update-collision-handling)
4. [Secrets Management](#secrets-management)
5. [Network Partition Scenarios](#network-partition-scenarios)
6. [Testing Strategy](#testing-strategy)
7. [Partial Update Recovery](#partial-update-recovery)
8. [Advanced Features](#advanced-features)
9. [Observability Architecture](#observability-architecture)
10. [Blast Radius Protection](#blast-radius-protection)

---

## Deployment Strategies

### Hybrid Event-Driven Pull Model

Devices combine long sleep windows with event signals:
- Each role defines a baseline `update_interval` (battery nodes default to 15-60 minutes, mains-powered gear stays near 30-120 seconds)
- Deployment Control service emits "update available" events via SSE/MQTT when a rollout segment is promoted
- Agents wake immediately on signal or when their interval elapses, ensuring NAT-friendly pulls without constant repo chatter
- All devices still perform self-managed convergence to maintain resilience

**Problem**: 100+ devices updating simultaneously can cause issues.

### Canary Deployment

Roll out to small percentage first:

```
Fleet Segments:
- Canary: 1-5% of fleet
- Early: 10-20% of fleet
- General: Remaining devices

Deployment Flow:
1. Push to main branch
2. Canary devices update immediately
3. Wait N minutes, monitor for failures
4. If healthy → release to Early segment
5. Wait N minutes, monitor
6. If healthy → release to General
7. If ANY segment fails → halt + rollback
```

**Implementation**:
- Each device has a `segment` identifier in config
- Central service tracks which segment can pull which commit
- Devices check eligibility before updating
- Manual promotion between segments

### Gradual Rollout

Alternative to segments - percentage-based rollout:

```
Time    Rollout %   Devices Updated
T+0     0%          0
T+5m    1%          ~10 devices
T+10m   5%          ~50 devices
T+20m   25%         ~250 devices
T+40m   100%        All devices
```

**Implementation**:
- Central service provides "rollout percentage"
- Device calculates: `hash(device_id + commit_hash) % 100`
- If result < rollout_percentage → eligible to update
- Provides deterministic but distributed updates

### Emergency Rollback

Fleet-wide version pinning:

```json
{
  "fleet_policy": {
    "forced_version": "abc123def",
    "reason": "Critical bug in v2.3.4",
    "expires": "2025-11-01T00:00:00Z"
  }
}
```

Devices ignore newer commits and revert to pinned version.

### Per-Device Override

Allow specific devices to:
- Stay on older version (demos, critical systems)
- Pull from different branch (staging, testing)
- Skip updates entirely (maintenance mode)

```json
{
  "device_id": "pi-camera-042",
  "override": {
    "branch": "staging",
    "version_lock": "xyz789abc",
    "auto_update": false
  }
}
```

---

## Config Drift Detection

Devices can drift from expected state due to:
- Manual changes
- SD card corruption
- Failed partial updates
- Docker state issues

### Reality Check System

Periodic validation of actual vs. expected state:

**What to Validate**:
- Current commit hash matches expected
- Docker containers running = compose definition
- Config file checksums match repository
- Required directories exist with correct permissions
- Network configuration matches template
- System packages at expected versions

**Validation Frequency**:
- Light check: Every 5 minutes (quick sanity)
- Deep check: Every hour (comprehensive)
- On-demand: Triggered from dashboard

**Drift Response**:
1. Detect drift
2. Log specifics to central system
3. Attempt self-heal:
   - Re-download configs
   - Restart containers
   - Fix file permissions
4. If self-heal fails → enter safe mode
5. Alert dashboard for manual intervention

### Checksum Verification

Critical files get SHA256 checksums:

```json
{
  "role": "camera-dual",
  "commit": "abc123",
  "checksums": {
    "docker-compose.yml": "sha256:abc...",
    "config/camera.conf": "sha256:def...",
    ".env": "sha256:ghi..."
  }
}
```

Agent verifies checksums on:
- Initial deployment
- Every deep validation check
- Before starting services

### Self-Healing Patterns

Common issues with automatic fixes:

| Issue | Detection | Fix |
|-------|-----------|-----|
| Container exited | `docker ps` check | `docker-compose up -d` |
| Config corruption | Checksum mismatch | Re-download from git |
| Permission drift | File stat check | `chmod`/`chown` reset |
| Disk full | `df` threshold | Cleanup old deployments |
| DNS failure | Health check fail | Restart networking |
| Time drift | NTP check | Force sync |

---

## Update Collision Handling

### Scenario: Rapid Commits

Developer pushes 3 commits in 2 minutes. Device is still deploying commit 1.

**Problem**:
- Queue all updates? (slow, may deploy broken middle versions)
- Skip to latest? (miss intermediate state testing)
- Cancel current? (leaves device in transition)

**Solution: Skip-to-Latest with Completion**:

```
Agent behavior:
1. Currently deploying commit A
2. Sees commit B available
3. Marks "pending update" to commit B
4. Completes commit A deployment
5. Validates commit A is healthy
6. Before next cycle, sees commit C available
7. Skips B entirely, deploys C
```

**Result**: Devices always reach stable state before next update.

### Update Throttling

Prevent update thrashing:

```
Rules:
- Minimum 5 minutes between update attempts
- Maximum 1 update per hour under normal conditions
- Failed updates pause for 15 minutes before retry
- 3 consecutive failures → enter safe mode
```

### Concurrent Update Lock

Prevent multiple agent instances:

```bash
# Agent acquires lock before update
flock -n /var/lock/fleet-agent.lock -c "perform_update"

# If lock held → skip this cycle
# Lock auto-releases on agent exit/crash
```

---

## Secrets Management

**Problem**: Pulling from public Git means configs are visible.

### Strategy 1: Encrypted Secrets in Repo

Use `age` or `sops` to encrypt sensitive files:

```bash
# In repository
roles/camera-dual/.env.encrypted
common/secrets.age

# On device
agent downloads encrypted file
agent decrypts using device-specific key
agent injects into environment
```

**Key Distribution**:
- Device public key generated on provision
- Private key stored in `/etc/fleet/device.key`
- Public key registered in central system
- Secrets encrypted to specific device keys

### Strategy 2: Secret Injection at Runtime

Separate secrets from config repo:

```
Config Repo (public): docker-compose.yml, scripts, code
Secrets Service: API for fetching runtime secrets

Agent flow:
1. Pull config from Git
2. Fetch secrets from API (authenticated via Tailscale)
3. Merge secrets into .env
4. Start services
```

**Benefits**:
- Secrets never in Git
- Can rotate without repo changes
- Audit logging of secret access

### Strategy 3: Tailscale + Vault

Best for production:

```
1. Device authenticated to Tailnet
2. Vault service on Tailnet (not public)
3. Device pulls secrets from Vault via Tailscale
4. Vault policies control which device gets which secrets
5. Secrets injected at container runtime
```

---

## Network Partition Scenarios

### Short Partition (< 5 minutes)

**Behavior**:
- Agent continues trying to reach Git
- Exponential backoff on retries
- Device continues running current version
- No alerts generated (transient issue)

### Medium Partition (5 minutes - 1 hour)

**Behavior**:
- Agent logs connectivity issue
- Reports "disconnected" status to dashboard (when reconnected)
- Continues running current services
- Health checks continue locally
- Device fully operational, just can't update

### Long Partition (> 1 hour)

**Behavior**:
- Device enters "isolated mode"
- Increases retry interval to every 5 minutes (reduce log spam)
- Marks itself as "stale" in local state
- When connection returns:
  - Verify time sync (NTP)
  - Check if commit hash changed
  - If yes → update with normal validation
  - Report outage duration to dashboard

### Permanent Partition

**Scenario**: Device loses internet permanently (e.g., airgapped network).

**Behavior**:
- After 24 hours disconnected → mark as "airgapped mode"
- Stop update attempts entirely
- Continue running current version indefinitely
- Remain fully functional for current role
- Manual update via USB/local mechanism

### Recovery Logic

When network returns after partition:

```python
def recover_from_partition(offline_duration):
    if offline_duration < 5min:
        # No special action
        resume_normal()

    elif offline_duration < 1hour:
        # Quick resync
        check_updates()
        report_status()

    elif offline_duration < 24hours:
        # Full resync
        verify_time_sync()
        validate_current_state()
        check_updates()
        deep_health_check()
        report_extended_outage()

    else:  # > 24 hours
        # Major resync
        alert_dashboard("extended_outage")
        verify_system_integrity()
        consider_full_revalidation()
        check_for_emergency_rollback()
```

---

## Testing Strategy

### Pre-Deployment Testing

**Staging Branch**:
```
Repository Branches:
- main: Production, all devices pull from here by default
- staging: Pre-production testing
- dev: Development work
```

**Staging Devices**:
- 1-3 devices configured to pull from `staging` branch
- Test all changes here before merging to `main`
- Automated validation on staging devices

### Syntax Validation in CI

GitHub Actions on every push:

```yaml
# .github/workflows/validate.yml
- Validate all docker-compose.yml files
- Check shell script syntax (shellcheck)
- Verify Python scripts (pylint, black)
- Validate JSON/YAML configs
- Check for secrets accidentally committed
- Run unit tests on agent code
```

### Role Validation Script

Every role includes `validate.sh`:

```bash
#!/bin/bash
# Validates role configuration before activation

check_required_files() {
  # Ensure all files exist
}

validate_compose_syntax() {
  # docker-compose config --quiet
}

check_environment_vars() {
  # Verify all required vars present
}

validate_network_config() {
  # Check ports, networks, volumes
}
```

Agent runs this BEFORE activating new role.

### Automated Health Checks

Post-deployment validation:

```python
# After deploying new version
wait(30 seconds)  # Allow services to start

checks = [
    check_containers_running(),
    check_http_endpoints_responding(),
    check_logs_for_errors(),
    check_resource_usage_normal(),
    check_role_specific_health()
]

if all(checks):
    mark_deployment_success()
else:
    automatic_rollback()
```

### Manual Testing Workflow

1. Developer pushes to `staging` branch
2. Staging devices auto-update
3. Dashboard shows staging device health
4. Manual smoke testing on staging
5. If good → merge `staging` to `main`
6. Production canary devices update first
7. Monitor, then roll out to fleet

---

## Partial Update Recovery

### Download Failures

**Scenario**: Network drops during git archive download.

**Recovery**:
```python
def download_with_recovery():
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            download_to_temp()
            verify_checksum()
            return success
        except DownloadError:
            cleanup_partial_download()
            wait(exponential_backoff(attempt))

    # All attempts failed
    log_error()
    keep_current_version()
```

### Extract Failures

**Scenario**: Corrupted tar file or disk full during extract.

**Recovery**:
```python
def safe_extract():
    check_disk_space()  # Need 2x archive size free

    try:
        extract_to(app_next)
        verify_extracted_checksums()
    except ExtractionError:
        cleanup_app_next()
        alert_dashboard("extraction_failed")
        keep_current_version()
```

### Validation Failures

**Scenario**: Files extracted but config is invalid.

**Recovery**:
```python
def validate_before_activate():
    if not run_validation_script():
        log_validation_errors()
        cleanup_app_next()
        alert_dashboard("validation_failed")
        keep_current_version()

    # Only proceed if validation passes
```

### Activation Failures

**Scenario**: Containers fail to start with new config.

**Recovery**:
```python
def activate_with_rollback():
    # Swap symlink
    atomic_swap(app_current, app_next)

    # Start services
    docker_compose_up()

    # Wait and verify
    sleep(30)

    if not all_services_healthy():
        # Automatic rollback
        atomic_swap(app_current, app_prev)
        docker_compose_up()
        alert_dashboard("activation_failed")
```

### Disk Space Protection

**Before any operation**:
```python
def check_resources():
    disk_free = get_disk_space_mb()
    download_size = get_archive_size_mb()

    required = download_size * 2  # Download + extract
    safety_margin = 500  # Keep 500MB free

    if disk_free < (required + safety_margin):
        # Cleanup old deployments
        cleanup_old_versions()

        if still_insufficient():
            alert_dashboard("disk_full")
            skip_update()
```

---

## Advanced Features

### Maintenance Windows

Some updates require reboots or extended downtime.

**Configuration**:
```json
{
  "device_id": "pi-camera-042",
  "maintenance_window": {
    "days": ["sunday"],
    "start": "02:00",
    "end": "06:00",
    "timezone": "UTC"
  }
}
```

**Agent Behavior**:
```python
if update_requires_reboot():
    if currently_in_maintenance_window():
        proceed_with_update()
    else:
        schedule_for_next_window()
```

### Version Locking

Pin specific devices to specific versions:

**Use Cases**:
- Demo devices that must not change
- Critical infrastructure during events
- Devices undergoing manual testing
- Temporary freeze for debugging

**Implementation**:
```json
{
  "device_id": "pi-camera-042",
  "version_lock": {
    "commit": "abc123def456",
    "reason": "Demo at conference, do not update",
    "locked_by": "user@example.com",
    "locked_until": "2025-11-15T00:00:00Z"
  }
}
```

Agent respects lock and refuses updates until expiry or manual unlock.

### Update History

Each device maintains local log:

```json
{
  "update_history": [
    {
      "timestamp": "2025-10-26T12:00:00Z",
      "from_commit": "abc123",
      "to_commit": "def456",
      "result": "success",
      "duration_seconds": 45
    },
    {
      "timestamp": "2025-10-26T11:00:00Z",
      "from_commit": "xyz789",
      "to_commit": "abc123",
      "result": "rollback",
      "reason": "containers_failed",
      "duration_seconds": 78
    }
  ]
}
```

**Benefits**:
- Debugging patterns ("this device always fails on Wednesdays")
- Audit trail
- Success rate metrics
- Performance monitoring

---

## Observability Architecture

### Metrics Stack

**Netdata** (on each device):
- CPU, memory, disk, network
- Docker container metrics
- Custom application metrics
- 1-second granularity

**Prometheus** (central):
- Scrapes Netdata exporters
- Long-term metric storage
- Alerting rules
- Federation for large fleets

**Grafana** (dashboard):
- Fleet overview boards
- Per-device drill-down
- Alert visualization
- Custom queries

### Logging Stack

**Device-level**:
```bash
# Agent logs to journald
journalctl -u fleet-agent -f

# Docker logs
docker-compose logs -f
```

**Central aggregation with Loki**:
```
Device → Promtail → Loki → Grafana

Labels:
- device_id
- role
- commit_hash
- environment (prod/staging)
```

**Log Levels**:
- DEBUG: Detailed operation flow
- INFO: Normal operations, updates
- WARN: Recoverable issues, retries
- ERROR: Failures requiring attention
- CRITICAL: Service down, safe mode

### Status Tracking

**Supabase Table Schema**:
```sql
CREATE TABLE devices (
    device_id TEXT PRIMARY KEY,
    hostname TEXT,
    role TEXT,
    commit_hash TEXT,
    last_seen TIMESTAMP,
    status TEXT,  -- healthy, degraded, safe_mode, offline
    agent_version TEXT,
    uptime_seconds INTEGER,
    last_update TIMESTAMP,
    last_update_result TEXT,
    current_error TEXT,
    ip_address TEXT,
    tailscale_ip TEXT,
    metadata JSONB
);
```

**Device reports every minute**:
```python
def report_status():
    post_to_supabase({
        "device_id": get_device_id(),
        "status": get_current_status(),
        "commit_hash": get_current_commit(),
        "last_seen": now(),
        "uptime_seconds": get_uptime(),
        # ... other fields
    })
```

### Dashboard Views

**Fleet Overview**:
```
Total Devices: 487
Online: 485 (99.6%)
Healthy: 480 (98.6%)
Degraded: 5 (1.0%)
Safe Mode: 2 (0.4%)
Offline: 2 (0.4%)

Current Commit: abc123def (95%)
             xyz789abc (5%)

Updates in last hour: 12
Failed updates: 0
Average update time: 42s
```

**Per-Device View**:
```
Device: pi-camera-042
Role: camera-dual
Status: Healthy ✓
Commit: abc123def456
Last Seen: 30 seconds ago
Uptime: 14 days
Last Update: 2 hours ago (success)

Resources:
CPU: 15%
Memory: 45%
Disk: 62%
Network: 2.5 Mbps

Quick Actions:
[View Logs] [Force Update] [Enter Safe Mode] [SSH]
```

---

## Blast Radius Protection

### Failure Detection

Monitor for correlated failures:

**Detection Logic**:
```python
def check_blast_radius():
    recent_failures = get_failures_last_N_minutes(5)
    total_devices = get_total_device_count()
    failure_rate = len(recent_failures) / total_devices

    thresholds = {
        "warning": 0.05,   # 5% failing
        "critical": 0.10,  # 10% failing
        "emergency": 0.20  # 20% failing
    }

    if failure_rate > thresholds["emergency"]:
        trigger_emergency_halt()
    elif failure_rate > thresholds["critical"]:
        halt_rollout()
        alert_team()
    elif failure_rate > thresholds["warning"]:
        slow_rollout()
        monitor_closely()
```

### Auto-Halt Mechanism

When blast radius detected:

```python
def emergency_halt():
    # Stop all ongoing rollouts
    set_rollout_percentage(0)

    # Pin fleet to last known good commit
    set_forced_version(get_last_stable_commit())

    # Alert
    send_alert("BLAST RADIUS DETECTED", {
        "failed_devices": get_failed_devices(),
        "failure_pattern": analyze_failures(),
        "suspected_commit": get_current_rollout_commit()
    })

    # Rollback failed devices
    for device in get_failed_devices():
        trigger_rollback(device)
```

### Failure Pattern Analysis

Detect what's actually broken:

```python
def analyze_failure_pattern(failures):
    patterns = {
        "same_role": are_all_same_role(failures),
        "same_error": are_all_same_error(failures),
        "same_network": are_all_same_network(failures),
        "same_hardware": are_all_same_hardware(failures),
        "same_timeframe": are_all_within_minutes(failures, 10)
    }

    if patterns["same_role"] and patterns["same_error"]:
        return "Role-specific config issue"
    elif patterns["same_error"] and patterns["same_timeframe"]:
        return "Code bug in update"
    elif patterns["same_network"]:
        return "Network infrastructure issue"
    else:
        return "Unknown pattern - investigate manually"
```

### Manual Override

Dashboard controls:

```
Emergency Controls:

[HALT ALL UPDATES]     - Stop entire fleet immediately
[ROLLBACK FLEET]       - Revert all to previous version
[PIN VERSION]          - Freeze at specific commit
[RESUME NORMAL]        - Return to auto-updates

Current Status: EMERGENCY HALT ACTIVE
Reason: 15% of fleet failing with "container_start_error"
Suspected Commit: abc123def
Time Since Halt: 5 minutes

Affected Devices: 73
Healthy Devices: 412

[View Failure Logs] [Analyze Pattern] [Test Fix on Staging]
```

---

## Summary

This architecture handles:

✅ Gradual rollouts with canary/segmented deployments
✅ Config drift detection and self-healing
✅ Update collisions and rapid commit scenarios
✅ Secrets management multiple strategies
✅ Network partitions from seconds to permanent
✅ Comprehensive testing before production
✅ Partial update recovery at every stage
✅ Maintenance windows and version locking
✅ Full observability with metrics, logs, status
✅ Blast radius protection with auto-halt

The system is designed to be **boring, reliable, and self-healing** - the three pillars of production fleet management.
