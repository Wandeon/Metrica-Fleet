# Metrica Fleet - Implementation Guide

This document outlines the phased approach to building Metrica Fleet, ordered by dependency and value delivery.

## Implementation Philosophy

**Build observability first, features second.**

You can't debug what you can't see. Starting with monitoring and logging means every subsequent component is visible during development and testing.

## Phase 0: Foundation (Week 1)

### Goals
- Establish development environment
- Create base infrastructure
- Set up testing capability

### Tasks

**1. Development Setup**
- [ ] Create test Raspberry Pi (or VM)
- [ ] Install base OS (Raspberry Pi OS Lite)
- [ ] Configure SSH access
- [ ] Install Docker and Docker Compose
- [ ] Set up Tailscale for secure access

**2. Repository Structure**
- [x] Initialize Git repository
- [x] Create directory structure
- [x] Add comprehensive documentation
- [ ] Set up GitHub Actions (validation only)

**3. Staging Branch**
- [ ] Create `staging` branch
- [ ] Configure one test device to track staging
- [ ] Document staging workflow

**Deliverable**: Test device pulling from repo, staging workflow documented.

---

## Phase 1: Observability Layer (Week 2-3)

### Goals
- See what's happening on devices
- Establish logging and metrics
- Create basic dashboard

### Components

**1.1 Safe Mode Stack**

The safety net for everything else.

```yaml
# common/safe-mode.yml
services:
  nginx:
    # Simple status page
  status-api:
    # Reports device state
  ssh:
    # Emergency access
```

**Tasks**:
- [ ] Create minimal Docker Compose stack
- [ ] Build simple status HTML page
- [ ] Create tiny API (Python Flask or Go)
- [ ] Test manual activation
- [ ] Document safe mode triggers

**1.2 Device Monitoring**

```
Stack: Netdata → Prometheus → Grafana
```

**Tasks**:
- [ ] Install Netdata on test device
- [ ] Configure Prometheus (central server)
- [ ] Set up Grafana
- [ ] Create basic dashboard
  - CPU, memory, disk metrics
  - Docker container status
  - Network traffic
- [ ] Test alert rules

**1.3 Log Aggregation**

```
Stack: Device logs → Promtail → Loki → Grafana
```

**Tasks**:
- [ ] Install Promtail on device
- [ ] Set up Loki (central)
- [ ] Configure log shipping
- [ ] Add log panels to Grafana
- [ ] Test log queries and filtering

**1.4 Status Tracking Database**

**Tasks**:
- [ ] Set up Supabase project (or PostgreSQL)
- [ ] Create device status schema
- [ ] Create API for status updates
- [ ] Build simple status reporting script
- [ ] Test device → database flow

**1.5 Basic Dashboard**

**Tasks**:
- [ ] Create web app (Next.js/React or simple HTML)
- [ ] Fetch device list from Supabase
- [ ] Display device status table
- [ ] Add device detail view
- [ ] Link to Grafana for metrics
- [ ] Link to Loki for logs

**Deliverable**: Can see device metrics, logs, and status without SSH.

---

## Phase 2: Basic Agent (Week 4-5)

### Goals
- Devices can pull from Git
- Validate configurations
- Report status
- NO SWAPPING YET - just detection

### Components

**2.1 Agent Core**

Simple agent that:
- Reads device config (role, branch)
- Checks Git for latest commit
- Compares with current version
- Reports findings to dashboard
- Does NOT deploy anything yet

**Language Choice**: Python (good libraries, easy to debug)

**Structure**:
```python
# scripts/agent.py

def main():
    config = load_device_config()
    current = get_current_commit()
    latest = fetch_latest_commit(config.branch)

    if latest != current:
        log("Update available: {} → {}".format(current, latest))
        report_status("update_available")
    else:
        log("Up to date: {}".format(current))
        report_status("healthy")

if __name__ == "__main__":
    main()
```

**Tasks**:
- [ ] Write basic agent script
- [ ] Add config file parsing
- [ ] Implement Git commit checking
- [ ] Add status reporting to Supabase
- [ ] Add proper logging
- [ ] Add timeout handling
- [ ] Test on staging device

**2.2 Systemd Service**

**Tasks**:
- [ ] Create `fleet-agent.service` template
- [ ] Create `fleet-agent.timer` for periodic runs
- [ ] Install on test device
- [ ] Verify journald logging
- [ ] Test start/stop/restart
- [ ] Verify it survives reboot

**2.3 Device Configuration**

```json
{
  "device_id": "pi-test-001",
  "hostname": "test-pi",
  "role": "camera-single",
  "branch": "staging",
  "update_interval": 900,
  "event_stream_url": "https://control.example.com/devices/pi-test-001/events",
  "segment": "canary"
}
```

**Tasks**:
- [ ] Define config schema
- [ ] Create config validator
- [ ] Add default config
- [ ] Document all fields (including event stream endpoints and interval overrides)
- [ ] Add config reload without restart
- [ ] Implement SSE/WebSocket listener that short-circuits the next poll when an update signal arrives

**Deliverable**: Agent honors long sleep intervals for low-power roles, wakes on event signals, detects updates, reports to dashboard. Nothing breaks.

---

## Phase 3: Atomic Deployment (Week 6-7)

### Goals
- Implement app_prev/current/next pattern
- Perform atomic swaps
- NO ROLLBACK YET

### Components

**3.1 Directory Structure**

```bash
/opt/fleet/
├── app_prev/          # Previous deployment
├── app_current/       # Symlink to active
├── app_next/          # Incoming deployment
├── agent/             # Agent code (not in deployment dirs)
└── config/            # Device config
```

**Tasks**:
- [ ] Create directory structure
- [ ] Set proper permissions
- [ ] Add cleanup script for old versions
- [ ] Document layout

**3.2 Download and Extract**

**Tasks**:
- [ ] Implement Git archive download
- [ ] Add checksum verification
- [ ] Implement extract to app_next
- [ ] Add disk space checking
- [ ] Add partial download cleanup
- [ ] Test with slow/failing network
- [ ] Add progress logging

**3.3 Validation**

**Tasks**:
- [ ] Create role validation script template
- [ ] Add docker-compose.yml syntax check
- [ ] Add .env validation
- [ ] Add checksum verification
- [ ] Run validation before swap
- [ ] Log validation failures
- [ ] Test with intentionally bad configs

**3.4 Atomic Swap**

**Tasks**:
- [ ] Implement symlink swap function
- [ ] Add atomic operations
- [ ] Test swap under load
- [ ] Verify Docker sees new files
- [ ] Add pre-swap backup of app_prev
- [ ] Test repeatedly

**3.5 Service Restart**

**Tasks**:
- [ ] Implement docker-compose down
- [ ] Implement docker-compose up
- [ ] Add wait for services to start
- [ ] Add timeout handling
- [ ] Log container status
- [ ] Test with various roles

**Deliverable**: Device can download, validate, swap, and restart services. Manual verification that it works.

---

## Phase 4: Rollback Logic (Week 8)

### Goals
- Detect failed deployments
- Automatic rollback to previous version
- Health check validation

### Components

**4.1 Health Checks**

**Tasks**:
- [ ] Define health check interface
- [ ] Implement container status check
- [ ] Implement HTTP endpoint checks
- [ ] Implement log error scanning
- [ ] Add role-specific health checks
- [ ] Set reasonable timeouts (30-60s)

**4.2 Post-Deployment Validation**

**Tasks**:
- [ ] Run health checks after swap
- [ ] Wait for grace period
- [ ] Check all containers running
- [ ] Check logs for critical errors
- [ ] Report health status
- [ ] Make pass/fail decision

**4.3 Automatic Rollback**

**Tasks**:
- [ ] Implement rollback function
- [ ] Swap back to app_prev
- [ ] Restart old services
- [ ] Verify rollback worked
- [ ] Log rollback event
- [ ] Alert dashboard
- [ ] Test with intentionally broken configs

**4.4 Rollback Testing**

**Test scenarios**:
- [ ] Container fails to start
- [ ] Container starts but crashes immediately
- [ ] HTTP endpoints return errors
- [ ] Config syntax error
- [ ] Missing environment variables
- [ ] Port conflicts

**Deliverable**: Device automatically recovers from bad deployments without manual intervention.

---

## Phase 5: Production Hardening (Week 9-10)

### Goals
- Handle all failure modes
- Add retry logic
- Network partition handling
- Convergence locking

### Tasks

**5.1 Retry with Backoff**
- [ ] Implement exponential backoff
- [ ] Add maximum retry limit
- [ ] Log retry attempts
- [ ] Test with intermittent failures

**5.2 Network Partition Handling**
- [ ] Detect prolonged disconnection
- [ ] Enter isolated mode
- [ ] Graceful degradation
- [ ] Recovery when network returns
- [ ] Test with firewall rules

**5.3 Convergence Locking**
- [ ] Implement flock-based locking
- [ ] Prevent overlapping runs
- [ ] Auto-cleanup stale locks
- [ ] Test concurrent executions

**5.4 Watchdog**
- [ ] Implement agent watchdog
- [ ] Detect hung agents
- [ ] Auto-restart on hang
- [ ] Test by forcing hangs

**5.5 Safe Mode Triggers**
- [ ] 3 consecutive failures → safe mode
- [ ] Manual trigger from dashboard
- [ ] Disk full → safe mode
- [ ] Critical errors → safe mode
- [ ] Test all triggers

**5.6 Update History**
- [ ] Log all update attempts
- [ ] Track success/failure
- [ ] Record timing
- [ ] Store locally
- [ ] Ship to central DB
- [ ] Add to dashboard

**Deliverable**: Agent handles all error cases gracefully. Zero cases requiring SSH.

---

## Phase 6: Advanced Deployment (Week 11-12)

### Goals
- Canary deployments
- Gradual rollouts
- Version locking
- Emergency controls

### Components

**6.1 Deployment Control Service**

Central service that controls rollout.

**Tasks**:
- [ ] Create API for rollout control
- [ ] Implement segment-based rollout
- [ ] Implement percentage-based rollout
- [ ] Add emergency halt
- [ ] Add version pinning
- [ ] Add per-device overrides

**6.2 Agent Integration**
- [ ] Query rollout service before update
- [ ] Respect segment assignments
- [ ] Honor version locks
- [ ] Check maintenance windows
- [ ] Test with various scenarios

**6.3 Dashboard Controls**
- [ ] Add rollout controls UI
- [ ] Show rollout progress
- [ ] Add emergency halt button
- [ ] Add version lock UI
- [ ] Add maintenance window UI
- [ ] Test all controls

**6.4 Blast Radius Protection**
- [ ] Implement failure detection
- [ ] Calculate failure rates
- [ ] Auto-halt on threshold
- [ ] Alert on anomalies
- [ ] Pattern analysis
- [ ] Test with simulated failures

**Deliverable**: Full control over fleet deployments. Can halt, rollback, or freeze fleet instantly.

---

## Phase 7: First Production Role (Week 13-14)

### Goals
- Create first real role
- Deploy to small fleet
- Validate entire system

### Tasks

**7.1 Camera Role**

Using your MasterCam device:

- [ ] Design docker-compose.yml for camera
- [ ] Add camera configuration
- [ ] Create validation script
- [ ] Add health checks
- [ ] Test on single device
- [ ] Document setup

**7.2 Deployment**
- [ ] Configure 3-5 devices as canary
- [ ] Deploy role to canaries
- [ ] Monitor for issues
- [ ] Expand to full fleet
- [ ] Validate all devices

**7.3 Monitoring**
- [ ] Add role-specific metrics
- [ ] Create Grafana dashboard
- [ ] Set up alerts
- [ ] Test alert delivery

**Deliverable**: First role running on real fleet with full observability.

---

## Phase 8: Additional Roles (Week 15+)

### Goals
- Template process for new roles
- Build remaining roles
- Documentation

### Roles to Build

1. **camera-single** - Single camera processing
2. **camera-dual** - Dual camera setup
3. **audio-player** - Audio streaming
4. **video-player** - Video playback
5. **zigbee-hub** - IoT hub
6. **ai-camera** - AI inference

**Per Role**:
- [ ] Define requirements
- [ ] Create docker-compose
- [ ] Add configurations
- [ ] Build validation
- [ ] Test on staging
- [ ] Deploy to production
- [ ] Create documentation

---

## Phase 9: Config Drift & Self-Healing (Week 16-17)

### Goals
- Detect drift
- Automatic repair
- Reality checks

### Tasks

**9.1 Drift Detection**
- [ ] Implement checksum verification
- [ ] Add Docker state checks
- [ ] Add file permission checks
- [ ] Add disk space checks
- [ ] Schedule periodic validation

**9.2 Self-Healing**
- [ ] Re-download corrupted files
- [ ] Restart failed containers
- [ ] Fix permissions
- [ ] Clean disk space
- [ ] Test common drift scenarios

**9.3 Deep Validation**
- [ ] Hourly reality check
- [ ] System integrity verification
- [ ] Config vs. actual comparison
- [ ] Report discrepancies

**Deliverable**: Fleet self-heals common issues without human intervention.

---

## Phase 10: Secrets Management (Week 18)

### Goals
- Secure secret distribution
- Encryption at rest
- Audit logging

### Implementation Options

Choose one based on needs:

**Option A: Encrypted in Repo (Simple)**
- [ ] Set up age/sops
- [ ] Encrypt secrets in repo
- [ ] Add decryption to agent
- [ ] Test secret rotation

**Option B: Vault Integration (Production)**
- [ ] Deploy Vault on Tailnet
- [ ] Configure Vault policies
- [ ] Integrate agent with Vault
- [ ] Test secret fetching
- [ ] Implement secret caching
- [ ] Add audit logging

**Deliverable**: Secrets distributed securely, never in plaintext.

---

## Phase 11: Scale Testing (Week 19-20)

### Goals
- Validate at scale
- Performance optimization
- Stress testing

### Tasks

**11.1 Load Testing**
- [ ] Simulate 100+ devices
- [ ] Test simultaneous updates
- [ ] Measure central service load
- [ ] Optimize bottlenecks

**11.2 Network Testing**
- [ ] Test with network delays
- [ ] Test with packet loss
- [ ] Test with bandwidth limits
- [ ] Verify graceful degradation

**11.3 Failure Testing**
- [ ] Test random device failures
- [ ] Test network partitions
- [ ] Test central service outages
- [ ] Verify recovery

**11.4 Performance Optimization**
- [ ] Profile agent resource usage
- [ ] Optimize update speed
- [ ] Reduce bandwidth usage
- [ ] Minimize disk writes

**Deliverable**: System validated at production scale with acceptable performance.

---

## Phase 12: Production Readiness (Week 21-22)

### Goals
- Complete documentation
- Runbooks
- Training materials
- Launch preparation

### Tasks

**12.1 Documentation**
- [ ] Complete architecture docs
- [ ] Write operator guide
- [ ] Write troubleshooting guide
- [ ] Document common issues
- [ ] Create FAQ

**12.2 Runbooks**
- [ ] Device provisioning procedure
- [ ] Update deployment procedure
- [ ] Emergency rollback procedure
- [ ] Adding new roles
- [ ] Scaling the fleet

**12.3 Automation**
- [ ] Device provisioning script
- [ ] SD card flashing tool
- [ ] Bulk operations scripts
- [ ] Backup/restore procedures

**12.4 Monitoring & Alerting**
- [ ] Define SLOs
- [ ] Configure all alerts
- [ ] Set up on-call rotation
- [ ] Test alert delivery
- [ ] Create escalation procedures

**12.5 Security Audit**
- [ ] Review authentication
- [ ] Check authorization
- [ ] Audit secret handling
- [ ] Verify network security
- [ ] Penetration testing

**Deliverable**: System ready for production use with complete operational procedures.

---

## Development Guidelines

### During Each Phase

**1. Test Thoroughly**
- Unit tests for code
- Integration tests for components
- End-to-end tests for workflows
- Break it intentionally

**2. Document as You Go**
- Code comments
- Architecture decisions
- Troubleshooting notes
- Lessons learned

**3. Monitor Everything**
- Add metrics for new features
- Log important events
- Update dashboards
- Set up alerts

**4. Review Before Proceeding**
- Does it work reliably?
- Are there edge cases?
- Is it documented?
- Can someone else understand it?

### Red Flags

Stop and fix if you see:

- ❌ SSH required to understand state
- ❌ Manual intervention for recovery
- ❌ Silent failures
- ❌ Inconsistent behavior
- ❌ Unclear error messages
- ❌ No way to monitor progress

### Success Criteria Per Phase

Before moving to next phase:

- ✅ All components working on test device
- ✅ Failure modes tested and handled
- ✅ Documented and reviewed
- ✅ Monitoring in place
- ✅ Staged to production successfully

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 0: Foundation | 1 week | Dev environment ready |
| 1: Observability | 2 weeks | Can see everything |
| 2: Basic Agent | 2 weeks | Detection working |
| 3: Atomic Deploy | 2 weeks | Updates working |
| 4: Rollback | 1 week | Self-healing |
| 5: Hardening | 2 weeks | Production-ready agent |
| 6: Advanced Deploy | 2 weeks | Full control |
| 7: First Role | 2 weeks | Real workload |
| 8: More Roles | 4+ weeks | Complete fleet |
| 9: Drift Detection | 2 weeks | Self-healing fleet |
| 10: Secrets | 1 week | Secure secrets |
| 11: Scale Testing | 2 weeks | Validated at scale |
| 12: Production | 2 weeks | Launch ready |

**Total: ~5-6 months for complete system**

**MVP (Phases 0-5): ~2 months**

---

## Notes

- Timeline assumes 1 developer full-time
- Add 50% buffer for real-world blockers
- Can parallelize some phases with team
- Skip advanced features for faster MVP

## Next Steps

1. Review this implementation plan
2. Adjust timeline based on resources
3. Set up Phase 0 environment
4. Begin Phase 1: Observability

**Remember**: Build observability first. Everything else depends on being able to see what's happening.
