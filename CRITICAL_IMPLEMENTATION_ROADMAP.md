# Critical Implementation Roadmap
**Enterprise-Grade Fleet Management System**
**50+ Device Deployment - Zero Tolerance for Failure**

---

## 🔴 CRITICAL UNDERSTANDING

**Current State:** Documentation only - 0% implementation
**Risk Level:** Cannot deploy to production
**Timeline to Production:** 4-5 months minimum
**Verification Required:** Every step must be monitored and tested

---

## THE NON-NEGOTIABLES

### 1. OBSERVABILITY FIRST
**Build monitoring BEFORE features**

```
Week 1-2: Deploy Full Monitoring Stack
├── Netdata on devices (system metrics)
├── Prometheus (central metrics)
├── Grafana (visualization)
└── Loki + Promtail (logs)

Verification:
✓ Can see CPU, memory, disk, network on all devices
✓ Logs queryable for 30 days
✓ Alerts fire within 3 minutes
✓ Dashboard shows fleet health at a glance
```

**Why This Matters:**
- Previous system failed because you couldn't see the failures
- Every component must be observable before it's deployable
- Can't debug what you can't see

---

### 2. SAFE MODE ALWAYS AVAILABLE
**The unkillable fallback configuration**

```
Week 2: Build Safe Mode Stack
├── Minimal Docker Compose (SSH + Netdata + logging)
├── Guaranteed to boot on any device
├── Always recoverable remotely
└── Entry point for recovery operations

Verification:
✓ Device boots to safe mode even with corrupted config
✓ SSH access works
✓ Metrics visible in Grafana
✓ Can deploy new config from safe mode
```

**Why This Matters:**
- With 50+ devices, you cannot physically access every device
- Safe mode is your insurance policy against bricking devices
- Every device must be remotely recoverable

---

### 3. FAILURE TESTING IS MANDATORY
**Test how it breaks before production**

```
Week 6-7: Chaos Engineering
├── Pull power during updates (10 times)
├── Fill disk during deployment
├── Corrupt config files
├── Disconnect network for 24 hours
├── Make Git unavailable
├── Create crash loops
├── Thermal throttling simulation
└── Clock skew testing

Verification:
✓ Every failure → graceful handling or recovery
✓ No permanent damage
✓ Logs explain what happened
✓ Alerts fire correctly
✓ Human knows what to do
```

**Why This Matters:**
- Production will be worse than you imagine
- Bad networks, power failures, heat are guaranteed
- System must survive chaos, not just work in ideal conditions

---

### 4. GRADUAL ROLLOUT ONLY
**Never update entire fleet simultaneously**

```
Update Strategy:
1. Deploy to canary device
2. Wait 15 minutes
3. Check health automatically
4. If OK → 5% of fleet
5. If OK → 25% of fleet
6. If OK → 100% of fleet
7. Halt immediately on >5% failure rate

Verification:
✓ Bad config only affects canary
✓ Automatic halt on failures
✓ Human can stop rollout instantly
✓ Rollback in <5 minutes
```

**Why This Matters:**
- One bad config can brick entire fleet
- Canary deployment catches issues early
- Emergency stop prevents cascading failures

---

### 5. REDUNDANCY EVERYWHERE
**No single point of failure**

```
Critical Redundancy:
├── Git: Primary (GitHub) + Mirror (local GitLab)
├── Monitoring: Prometheus alerts + external heartbeat
├── Network: Retry logic + exponential backoff
├── Power: Graceful shutdown on low voltage
└── Storage: Keep previous working version always

Verification:
✓ Primary Git down → automatic failover
✓ Monitoring down → external alerts still work
✓ Network partition → devices run safely
✓ Power loss → boots to last working version
```

**Why This Matters:**
- Single points of failure will fail
- External dependencies (GitHub) will have outages
- System must survive partial failures

---

## IMPLEMENTATION PHASES (CRITICAL PATH)

### ✅ PHASE 0: FOUNDATION (Week 1)
**Current Status: Partially Complete**

**Build:**
- [x] Git repository created
- [x] Documentation written
- [ ] Test Raspberry Pi set up
- [ ] Docker installed and verified
- [ ] Base OS configured

**Deliverable:** One working test device

---

### 🔴 PHASE 1: OBSERVABILITY (Week 2-3)
**Status: NOT STARTED - HIGHEST PRIORITY**

**Build:**
1. Deploy Netdata on test device
2. Set up Prometheus server
3. Set up Grafana server
4. Configure Loki + Promtail
5. Create first dashboard

**Deliverable:** Can see device metrics and logs in Grafana

**Verification:**
```bash
# These must all work:
curl http://device:19999/api/v1/info  # Netdata
curl http://prometheus:9090/api/v1/query?query=up  # Prometheus
curl http://grafana:3000/api/health  # Grafana
# Logs visible in Loki within 30 seconds
```

**Why This First:**
- Cannot build anything else without visibility
- Need metrics before writing agent
- Dashboard needed for fleet management

---

### 🔴 PHASE 2: SAFE MODE (Week 3)
**Status: NOT STARTED - CRITICAL**

**Build:**
```yaml
# /opt/fleet/safe-mode/docker-compose.yml
version: "3.8"
services:
  netdata:
    image: netdata/netdata
    restart: always

  promtail:
    image: grafana/promtail
    restart: always
```

**Deliverable:** Unkillable baseline configuration

**Verification:**
- ✓ Device boots to safe mode
- ✓ Can SSH in
- ✓ Metrics visible in Grafana
- ✓ Corrupt main config → safe mode activates

**Why This First:**
- Your insurance policy against bricking devices
- Must exist before any update mechanism
- Foundation for recovery operations

---

### 🔴 PHASE 3: BASIC AGENT (Week 4-5)
**Status: NOT STARTED**

**Build:**
```python
# /opt/fleet/agent/metrica_agent.py
def main():
    config = read_config()
    current_hash = get_current_commit()
    latest_hash = fetch_git_commit(config.branch)

    if latest_hash != current_hash:
        log.info("Update available", current=current_hash, latest=latest_hash)
        metrics.update_available.set(1)
    else:
        log.info("Up to date")
        metrics.update_available.set(0)
```

**Deliverable:** Agent that detects updates (doesn't apply yet)

**Verification:**
- ✓ Agent runs every 60 seconds
- ✓ Logs visible in Loki
- ✓ Metrics in Prometheus
- ✓ Crash loop protection works

**Why This Order:**
- Start simple: detection before deployment
- Test monitoring integration
- Build confidence before risky operations

---

### 🔴 PHASE 4: ATOMIC DEPLOYMENT (Week 6-7)
**Status: NOT STARTED - HIGH RISK**

**Build:**
```python
def apply_update(latest_hash):
    with file_lock("/opt/fleet/update.lock"):
        check_disk_space(required_mb=500)
        download_archive(latest_hash, "/opt/app_next")
        validate_config("/opt/app_next/docker-compose.yml")

        # Atomic swap
        os.symlink("/opt/app_next", "/opt/app_current_new")
        os.rename("/opt/app_current_new", "/opt/app_current")

        restart_docker_compose()
        if not health_check():
            rollback()
```

**Deliverable:** Agent can update itself atomically

**Verification:**
- ✓ Git commit → device updates in <5 min
- ✓ Bad config → automatic rollback
- ✓ Power loss during update → boots to previous
- ✓ Concurrent updates impossible (lock works)

**Why This Is Risky:**
- Race conditions possible
- Filesystem operations can fail
- Power loss can corrupt state
- **MUST test extensively before production**

---

### 🔴 PHASE 5: FAILURE TESTING (Week 7-8)
**Status: NOT STARTED - MANDATORY**

**Tests to Run:**

```bash
# Test 1: Power failure during update
while true; do
    trigger_update()
    sleep $RANDOM_0_TO_60_SECONDS
    cut_power()  # GPIO-controlled relay
    wait_for_boot()
    verify_device_healthy()
done

# Run 10 times, verify:
# ✓ Device always boots
# ✓ Either old or new version (never broken)
# ✓ Logs explain what happened
```

```bash
# Test 2: Disk full
fill_disk_to_90_percent()
trigger_update()
verify_graceful_failure()
verify_device_still_works()
verify_alert_fired()
```

```bash
# Test 3: Network partition
disconnect_network()
wait_24_hours()
reconnect_network()
verify_device_syncs()
```

**Deliverable:** Confidence system survives chaos

**Why This Is Critical:**
- Previous system failed because this was skipped
- Real world is chaotic
- Better to find issues in testing than production

---

### 🟡 PHASE 6: FLEET DASHBOARD (Week 9-10)
**Status: NOT STARTED**

**Build:**
```
Database (Supabase):
  - devices table (status, version, last_seen)

Dashboard (React/Vue/Svelte):
  - Fleet overview (health %, version distribution)
  - Device list (sortable, filterable)
  - Device detail (metrics, logs, SSH button)
  - Emergency stop button

Agent:
  - POST status every 60s
```

**Deliverable:** Web UI to manage fleet

**Verification:**
- ✓ Shows all devices
- ✓ Real-time updates
- ✓ Emergency stop halts all updates
- ✓ Can view logs per device

---

### 🟡 PHASE 7: CANARY DEPLOYMENT (Week 11-12)
**Status: NOT STARTED**

**Build:**
```python
def deploy_update(commit_hash):
    # Stage 1: Canary
    deploy_to_devices(canary_devices, commit_hash)
    wait_minutes(15)
    if health_check_failed(canary_devices):
        emergency_stop()
        return

    # Stage 2: 5%
    deploy_to_devices(sample_5_percent(), commit_hash)
    wait_minutes(15)
    if health_check_failed():
        emergency_stop()
        return

    # Stage 3: 25%
    # Stage 4: 100%
```

**Deliverable:** Safe fleet-wide updates

---

### 🟡 PHASE 8: GIT REDUNDANCY (Week 13)
**Status: NOT STARTED**

**Build:**
```yaml
Agent Config:
  git_endpoints:
    - https://github.com/Wandeon/Metrica-Fleet (primary)
    - https://gitlab.local/metrica-fleet (mirror)

  failover_timeout: 30s
```

**Deliverable:** No single point of failure on Git

---

### 🔴 PHASE 9: PRODUCTION PILOT (Week 14-15)
**Status: NOT STARTED - CRITICAL GATE**

**Deploy to 5 devices for 2 weeks:**
- Different roles (camera, sensor, gateway)
- Different locations
- Monitor 24/7
- Perform chaos tests in production
- Collect failure data

**Go/No-Go Decision:**
- If 99% uptime → proceed to full rollout
- If <99% uptime → stop and fix issues

**Why This Matters:**
- Real world always surprises
- Small scale catches issues before they affect 50 devices
- Learn lessons cheaply

---

### 🔴 PHASE 10: FULL ROLLOUT (Week 16-19)
**Status: NOT STARTED**

**Gradual Deployment:**
- Week 16: 10 devices (20%)
- Week 17: 25 devices (50%)
- Week 18: 40 devices (80%)
- Week 19: 50+ devices (100%)

**Halt Conditions:**
- >5% failure rate → stop rollout
- Unexpected behavior → investigate
- User reports issues → pause and assess

**Deliverable:** Entire fleet managed automatically

---

## VERIFICATION REQUIREMENTS (BEFORE PRODUCTION)

### Reliability Checklist
- [ ] 30 days continuous operation (no human intervention)
- [ ] 99.9% uptime SLA (max 43 min downtime/month)
- [ ] 100 consecutive successful updates
- [ ] All chaos tests passed
- [ ] Zero permanent failures (all recovered automatically)

### Observability Checklist
- [ ] Every device reporting metrics every 60s
- [ ] Logs queryable for 30 days
- [ ] Alerts firing within 3 minutes
- [ ] Dashboard loads <2s with 50 devices
- [ ] No blind spots (every failure has alert)

### Security Checklist
- [ ] No secrets in Git (automated scan)
- [ ] All secrets encrypted
- [ ] Audit trail of all deployments
- [ ] Device authentication required
- [ ] Security testing passed

### Operational Readiness
- [ ] Runbooks for common failures
- [ ] On-call trained
- [ ] Disaster recovery tested
- [ ] Escalation procedures documented

---

## CRITICAL FAILURE MODES TO MONITOR

**Every deployment must verify these are handled:**

1. **Git Unavailable**
   - Alert: Git fetch failures >3
   - Action: Automatic failover to mirror
   - Recovery: Continue with cached version

2. **Agent Crash Loop**
   - Alert: >3 restarts in 5 minutes
   - Action: Enter safe mode
   - Recovery: Manual investigation

3. **Disk Full**
   - Alert: <500MB free space
   - Action: Skip updates, cleanup old images
   - Recovery: Free space, resume updates

4. **Network Partition**
   - Alert: >15 min no connectivity
   - Action: Continue running current version
   - Recovery: Resync on reconnection

5. **Bad Config Deployed**
   - Alert: Canary health check failed
   - Action: Halt rollout, rollback canary
   - Recovery: Fix config, redeploy

6. **Thermal Shutdown**
   - Alert: CPU temp >80°C
   - Action: Reduce workload, throttle updates
   - Recovery: Cool down, resume

7. **Update Stuck**
   - Alert: Update running >15 min
   - Action: Kill process, rollback
   - Recovery: Investigate logs, retry

8. **Config Drift**
   - Alert: Checksum mismatch
   - Action: Re-download config
   - Recovery: Validate and redeploy

9. **Monitoring Down**
   - Alert: External heartbeat missed
   - Action: Human investigation
   - Recovery: Restart monitoring stack

10. **Fleet-Wide Failure**
    - Alert: >20% devices unhealthy
    - Action: EMERGENCY STOP all updates
    - Recovery: Manual incident response

---

## DEVELOPMENT ENVIRONMENT REQUIREMENTS

### Hardware Needed
- 3 Raspberry Pi (test, staging, canary)
- Power control relay (for power-loss testing)
- Network switch with VLAN (for partition testing)
- Heat source (for thermal testing)
- Monitoring server (can be VM)

### Software Stack
```yaml
Devices:
  - Raspberry Pi OS Lite
  - Docker + Docker Compose
  - systemd
  - Python 3.11+

Monitoring Server:
  - Ubuntu/Debian
  - Prometheus
  - Grafana
  - Loki
  - GitLab/Gitea (Git mirror)

Development:
  - Git
  - Python 3.11+
  - Docker Desktop
  - pytest (testing)
  - GitHub Actions (CI/CD)
```

---

## DAILY OPERATIONS (POST-DEPLOYMENT)

### Morning Checklist
- [ ] Check dashboard for fleet health
- [ ] Review overnight alerts
- [ ] Verify all devices checked in last hour
- [ ] Check update success rate >99%

### Weekly Tasks
- [ ] Review logs for anomalies
- [ ] Check disk space trends
- [ ] Verify backup integrity
- [ ] Review and update runbooks

### Monthly Tasks
- [ ] Generate uptime report
- [ ] Review incident post-mortems
- [ ] Update security patches
- [ ] Test disaster recovery procedure

---

## INCIDENT RESPONSE PROCEDURES

### P1 (Critical): Fleet-Wide Failure
1. Press emergency stop button
2. Page on-call engineer
3. Assess scope (how many devices affected)
4. Rollback to last known good config
5. Investigate root cause
6. Deploy fix to canary
7. Gradual rollout of fix

### P2 (High): Single Device Failure
1. Check device logs in dashboard
2. Attempt automatic recovery (reboot)
3. If persistent, enter safe mode
4. SSH in for manual investigation
5. Fix and redeploy

### P3 (Medium): Degraded Performance
1. Review metrics for anomalies
2. Check resource usage
3. Investigate application logs
4. Deploy fix in next update window

---

## SUCCESS METRICS

**These numbers must be met for production readiness:**

- **Uptime:** 99.9% (max 43 min downtime/month)
- **Update Success Rate:** 99% (max 1 failure per 100 updates)
- **Alert False Positive Rate:** <5% (alerts must be actionable)
- **Mean Time to Detection:** <3 minutes (from failure to alert)
- **Mean Time to Recovery:** <15 minutes (from alert to fixed)
- **Dashboard Load Time:** <2 seconds
- **Update Latency:** <5 minutes (commit to deployed)
- **Agent CPU Usage:** <5% average
- **Agent Memory Usage:** <100MB
- **Network Usage:** <100MB/day per device

---

## FINAL CHECKLIST BEFORE PRODUCTION

**DO NOT DEPLOY until ALL items are ✓:**

### Implementation
- [ ] All code written and tested
- [ ] All monitoring configured
- [ ] All alerts defined and tested
- [ ] All runbooks written
- [ ] All documentation updated

### Testing
- [ ] Unit tests passing (100% coverage critical paths)
- [ ] Integration tests passing
- [ ] Chaos tests passing (all 10 failure modes)
- [ ] Load tests passing (50 devices)
- [ ] Soak test passing (30 days)

### Operational
- [ ] On-call trained on system
- [ ] Escalation procedures documented
- [ ] Disaster recovery tested
- [ ] Backup and restore tested
- [ ] Incident response procedures tested

### Security
- [ ] Security scan passing
- [ ] No secrets in Git
- [ ] Secrets rotation working
- [ ] Audit trail verified
- [ ] Access control tested

### Compliance
- [ ] Uptime SLA verified
- [ ] Data retention policy enforced
- [ ] Audit requirements met
- [ ] Documentation complete

---

## TIMELINE SUMMARY

```
Week 1:    Foundation (test environment)
Week 2-3:  Observability stack (CRITICAL)
Week 3:    Safe mode (CRITICAL)
Week 4-5:  Basic agent (update detection)
Week 6-7:  Atomic deployment (HIGH RISK)
Week 7-8:  Failure testing (MANDATORY)
Week 9-10: Dashboard
Week 11-12: Canary deployment
Week 13:   Git redundancy
Week 14-15: Production pilot (5 devices)
Week 16-19: Full rollout (gradual)

Total: 16-19 weeks (4-5 months)
```

**NO SHORTCUTS ALLOWED**
- Skipping failure testing = production disaster
- Skipping observability = debugging nightmare
- Skipping safe mode = bricked devices
- Skipping gradual rollout = fleet-wide failure

---

## CONTACT AND ESCALATION

### Normal Hours
- Monitor dashboard daily
- Review alerts weekly
- Respond to P2/P3 within 4 hours

### After Hours
- P1 (Critical): Page on-call immediately
- P2 (High): Email, respond next business day
- P3 (Medium): Log for weekly review

### Emergency Contacts
- On-Call Engineer: [TBD]
- Backup: [TBD]
- Escalation: [TBD]

---

**This roadmap is your contract with reliability.**

Every checkbox is a promise that the system will work.
Every verification is proof that it actually does.
Every test is insurance against production failure.

**The previous system failed because these steps were skipped.**
**This one will succeed because every step is verified.**

Build it right, or don't build it at all.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-10
**Next Review:** After Phase 1 completion
**Status:** Ready to begin implementation
