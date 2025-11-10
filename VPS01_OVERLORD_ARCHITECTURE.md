# VPS-01 Overlord: Central Fleet Management Server
**The Brain of the Metrica Fleet**

**Document Version:** 1.0
**Date:** 2025-11-10
**Status:** Architecture Design
**Purpose:** Centralized monitoring, management, and observability for 50+ device fleet

---

## EXECUTIVE SUMMARY

**VPS-01 "Overlord"** is the central management server that unifies all monitoring, alerting, and fleet management capabilities. It acts as the single pane of glass for the entire Metrica Fleet.

**Key Principle:** 🚨 **VPS-01 failure must NOT cause fleet failure**
- Devices operate independently even if Overlord is down
- VPS-01 provides observability, not functionality
- Loss of Overlord = temporary blindness, not fleet outage

---

## PART 1: ARCHITECTURAL ROLE

### What VPS-01 Does

```
VPS-01 "Overlord"
├── Monitoring Infrastructure
│   ├── Prometheus (metrics aggregation)
│   ├── Grafana (visualization + dashboards)
│   ├── Loki (log aggregation)
│   └── Alertmanager (alert routing)
│
├── Fleet Management
│   ├── PostgreSQL/Supabase (device status database)
│   ├── Dashboard UI (React/Vue web interface)
│   ├── Git Mirror (GitLab/Gitea for redundancy)
│   └── API Server (fleet management endpoints)
│
├── Security Services
│   ├── Vault (secrets management)
│   ├── Certificate Authority (device TLS certs)
│   └── Authentication (SSO/OAuth)
│
├── Operational Tools
│   ├── Backup Manager (automated backups)
│   ├── Update Orchestrator (canary deployment logic)
│   ├── Health Check Aggregator
│   └── Dead Man's Switch Monitor
│
└── External Integrations
    ├── Email/SMS alerts
    ├── Slack/Discord webhooks
    ├── PagerDuty/Opsgenie
    └── External monitoring (UptimeRobot)
```

### What VPS-01 Does NOT Do

❌ **Does NOT run device workloads** (cameras, sensors stay on Pi devices)
❌ **Does NOT proxy device traffic** (devices communicate directly)
❌ **Does NOT block device operations** (devices work offline)
❌ **Does NOT hold critical runtime data** (devices are source of truth)

---

## PART 2: HARDWARE REQUIREMENTS

### Recommended Specifications

**For 50-100 Device Fleet:**

```yaml
VPS Provider: Hetzner, DigitalOcean, Vultr, OVH
Region: Same continent as fleet (low latency)
Datacenter: Choose 2 for redundancy (primary + backup)

Primary VPS-01:
  CPU: 4 vCPU (ARM or x86-64, ARM preferred for cost)
  RAM: 8 GB (Prometheus + Grafana + Loki + PostgreSQL)
  Disk: 200 GB SSD (metrics retention + logs)
  Network: 1 Gbps (sufficient for 100 devices @ 1KB/s each)
  IPv4: 1 static IP
  IPv6: /64 subnet (optional)
  Estimated Cost: $20-40/month

Backup VPS-02 (optional but recommended):
  CPU: 2 vCPU
  RAM: 4 GB
  Disk: 100 GB SSD
  Purpose: Failover monitoring, Git mirror, backup database
  Estimated Cost: $10-20/month

Total Monthly Cost: $30-60/month
```

**Scaling for Larger Fleets:**

| Fleet Size | CPU | RAM | Disk | Cost/Month |
|------------|-----|-----|------|------------|
| 50 devices | 4 vCPU | 8 GB | 200 GB | $30 |
| 100 devices | 6 vCPU | 16 GB | 400 GB | $60 |
| 250 devices | 8 vCPU | 32 GB | 1 TB | $120 |
| 500 devices | 16 vCPU | 64 GB | 2 TB | $250 |

### Storage Breakdown

```
Prometheus Metrics:
  - 100 devices × 100 metrics × 15-day retention
  - ~50 GB (with compression)

Loki Logs:
  - 100 devices × 1 MB/day × 30-day retention
  - ~3 GB (with compression)

PostgreSQL Database:
  - Device status table: <100 MB
  - Historical data (1 year): ~10 GB

Grafana:
  - Dashboards + settings: <1 GB

Git Mirror:
  - Repository history: ~5 GB

Docker Images:
  - All services: ~20 GB

Operating System:
  - Ubuntu 24.04 LTS: ~5 GB

Backups (on separate storage):
  - Daily database dumps: 1 GB/day × 30 days = 30 GB
  - Configuration backups: <1 GB

Total: ~95 GB used, 200 GB allocated (room for growth)
```

---

## PART 3: SOFTWARE STACK

### Operating System

```yaml
OS: Ubuntu 24.04 LTS Server (ARM64 or AMD64)
Why:
  - 5 years support (until 2029)
  - Excellent Docker support
  - Large community
  - Automatic security updates

Initial Setup:
  - Minimal server installation
  - SSH key authentication only (no password)
  - Firewall (ufw) enabled
  - Automatic security updates (unattended-upgrades)
  - Fail2ban for SSH protection
  - NTP time synchronization
```

### Core Services (Docker Compose)

```yaml
# /opt/overlord/docker-compose.yml
version: "3.8"

services:
  # ============================================
  # MONITORING STACK
  # ============================================

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: always
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=90d'  # 90 days retention
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    ports:
      - "9090:9090"
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: always
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=https://overlord.example.com
    ports:
      - "3000:3000"
    networks:
      - monitoring

  loki:
    image: grafana/loki:latest
    container_name: loki
    restart: always
    volumes:
      - ./loki:/etc/loki
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    ports:
      - "3100:3100"
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    restart: always
    volumes:
      - ./alertmanager:/etc/alertmanager
    command:
      - '--config.file=/etc/alertmanager/config.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    networks:
      - monitoring

  # ============================================
  # DATABASE
  # ============================================

  postgres:
    image: postgres:16-alpine
    container_name: postgres
    restart: always
    environment:
      - POSTGRES_DB=metrica_fleet
      - POSTGRES_USER=metrica
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    networks:
      - database

  # ============================================
  # GIT MIRROR
  # ============================================

  gitea:
    image: gitea/gitea:latest
    container_name: gitea
    restart: always
    environment:
      - USER_UID=1000
      - USER_GID=1000
      - GITEA__database__DB_TYPE=postgres
      - GITEA__database__HOST=postgres:5432
      - GITEA__database__NAME=gitea
      - GITEA__database__USER=metrica
      - GITEA__database__PASSWD=${POSTGRES_PASSWORD}
    volumes:
      - gitea_data:/data
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "3001:3000"
      - "222:22"
    networks:
      - database
      - web

  # ============================================
  # FLEET DASHBOARD
  # ============================================

  dashboard:
    image: metrica/dashboard:latest  # Custom built
    container_name: dashboard
    restart: always
    environment:
      - DATABASE_URL=postgresql://metrica:${POSTGRES_PASSWORD}@postgres:5432/metrica_fleet
      - PROMETHEUS_URL=http://prometheus:9090
      - LOKI_URL=http://loki:3100
    ports:
      - "8080:8080"
    networks:
      - database
      - monitoring
      - web

  # ============================================
  # REVERSE PROXY (SSL termination)
  # ============================================

  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: always
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    networks:
      - web

  # ============================================
  # SECRETS MANAGEMENT (Optional, Phase 2)
  # ============================================

  # vault:
  #   image: hashicorp/vault:latest
  #   container_name: vault
  #   restart: always
  #   cap_add:
  #     - IPC_LOCK
  #   volumes:
  #     - ./vault/config:/vault/config
  #     - vault_data:/vault/file
  #   command: server
  #   ports:
  #     - "8200:8200"
  #   networks:
  #     - web

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
  postgres_data:
  gitea_data:
  vault_data:

networks:
  monitoring:
  database:
  web:
```

### Service Purpose Matrix

| Service | Purpose | Critical? | Depends On | Fallback |
|---------|---------|-----------|------------|----------|
| **Prometheus** | Metrics collection | Yes | None | External Grafana Cloud |
| **Grafana** | Visualization | Yes | Prometheus, Loki | Direct Prometheus query |
| **Loki** | Log aggregation | Medium | None | Device local logs |
| **Alertmanager** | Alert routing | Yes | Prometheus | Email directly from Prometheus |
| **PostgreSQL** | Device status DB | Yes | None | Read-only mode |
| **Gitea** | Git mirror | Medium | PostgreSQL | GitHub primary |
| **Dashboard** | Fleet UI | Medium | All | CLI management |
| **Nginx** | Reverse proxy + SSL | Yes | None | Direct service access |

---

## PART 4: CRITICAL FAILURE MODES

### The Overlord's Achilles' Heels

**⚠️ WARNING:** VPS-01 becomes a **single point of failure for observability**

#### Failure Mode 1: VPS-01 Total Outage

**Scenario:** VPS goes offline (provider outage, network failure, system crash)

**Impact:**
- ❌ No metrics visibility
- ❌ No log aggregation
- ❌ No alerts firing
- ❌ No dashboard access
- ✅ **Devices continue operating normally**
- ✅ Devices continue updating from GitHub

**Mitigation:**
```yaml
BEFORE Failure:
  - Backup VPS-02 in different datacenter
  - External monitoring (UptimeRobot pings VPS-01)
  - Dead man's switch (VPS-01 must ping external service every 5 min)

DURING Failure:
  - Devices queue status updates locally
  - Devices continue operating on last known config
  - External alerts fire ("VPS-01 unreachable")
  - Automatic failover to VPS-02 (if configured)

AFTER Recovery:
  - Devices replay queued status updates
  - Prometheus backfills metrics (from device Netdata)
  - Logs recovered from journald on devices
```

**Verification:**
- [ ] VPS-01 powered off → external alert fires within 5 min
- [ ] Devices continue operating normally
- [ ] VPS-01 restored → devices reconnect automatically
- [ ] No data loss (metrics and logs recovered)

---

#### Failure Mode 2: Database Corruption

**Scenario:** PostgreSQL data corruption, disk failure

**Impact:**
- ❌ Cannot see device status
- ❌ Dashboard shows errors
- ✅ Monitoring still works (Prometheus independent)
- ✅ Devices continue operating

**Mitigation:**
```yaml
PREVENTION:
  - Daily automated backups (pg_dump)
  - Transaction logging (WAL archiving)
  - Filesystem snapshots (if supported)
  - RAID if using dedicated server

DETECTION:
  - PostgreSQL health checks every 60s
  - Alert on connection failures
  - Alert on slow queries (>1s)

RECOVERY:
  - Restore from latest backup (max 24h data loss)
  - Rebuild database from device status API
  - Use Prometheus as source of truth for historical data
```

**Recovery Time Objective (RTO):** 1 hour
**Recovery Point Objective (RPO):** 24 hours

---

#### Failure Mode 3: Prometheus Metrics Storage Full

**Scenario:** Disk fills up, Prometheus cannot write new metrics

**Impact:**
- ❌ No new metrics stored
- ❌ Gaps in historical data
- ⚠️ Alerting may break
- ✅ Devices continue operating

**Mitigation:**
```yaml
PREVENTION:
  - Disk usage monitoring (alert at 80%)
  - Automatic cleanup of old metrics (90-day retention)
  - Compression enabled
  - Reserved disk space (10% minimum)

DETECTION:
  - Prometheus health endpoint check
  - Disk space metric alert
  - Alert on TSDB errors

IMMEDIATE RESPONSE:
  - Reduce retention period (90d → 30d)
  - Delete oldest data blocks
  - Scale up disk size
```

**Automation:**
```bash
# Automatic cleanup when disk >90% full
if df /var/lib/prometheus | awk 'NR==2 {print $5}' | sed 's/%//' | awk '{if($1>90) exit 0; else exit 1}'; then
  echo "Disk critical, purging old metrics"
  find /var/lib/prometheus/data -type d -mtime +30 -exec rm -rf {} \;
fi
```

---

#### Failure Mode 4: Monitoring Stack Overwhelmed

**Scenario:** Too many devices, too many metrics, VPS-01 CPU/RAM saturated

**Impact:**
- ⚠️ Slow queries
- ⚠️ Dashboard timeouts
- ⚠️ Alerts delayed
- ✅ Devices continue operating

**Mitigation:**
```yaml
PREVENTION:
  - Rate limiting on metrics ingestion
  - Downsampling (1s → 15s granularity for old data)
  - Metric cardinality limits
  - Resource limits on containers

DETECTION:
  - CPU usage >80% for 5 min → alert
  - Memory usage >80% → alert
  - Query latency >5s → alert

SCALING:
  - Vertical: Upgrade VPS size (4 vCPU → 8 vCPU)
  - Horizontal: Prometheus federation (multiple instances)
  - Optimization: Remove unused metrics, reduce retention
```

**Capacity Planning:**
| Devices | Metrics/Device | Total Series | RAM Needed | CPU Needed |
|---------|----------------|--------------|------------|------------|
| 50 | 100 | 5,000 | 4 GB | 2 vCPU |
| 100 | 100 | 10,000 | 8 GB | 4 vCPU |
| 250 | 100 | 25,000 | 16 GB | 8 vCPU |
| 500 | 100 | 50,000 | 32 GB | 16 vCPU |

---

#### Failure Mode 5: Network Partition (VPS ↔ Devices)

**Scenario:** Network between VPS-01 and devices lost (firewall, ISP issue)

**Impact:**
- ❌ Devices cannot report status
- ❌ No metrics ingestion
- ❌ No log shipping
- ✅ Devices continue operating
- ✅ Devices continue updating (GitHub still reachable)

**Mitigation:**
```yaml
PREVENTION:
  - Multiple network paths (primary + backup)
  - VPN mesh (Tailscale for all devices)
  - Public IP + VPN endpoint redundancy

DETECTION:
  - Prometheus target down alerts
  - Device last_seen timestamp alerts
  - External connectivity monitoring

HANDLING:
  - Devices queue updates locally (up to 7 days)
  - On reconnection, devices replay queued data
  - Prometheus scrapes device Netdata directly when reachable
```

---

#### Failure Mode 6: SSL Certificate Expiry

**Scenario:** Let's Encrypt cert expires, auto-renewal fails

**Impact:**
- ❌ Dashboard inaccessible (browser blocks)
- ⚠️ Devices may reject HTTPS connections
- ✅ Monitoring still works (internal network)

**Mitigation:**
```yaml
PREVENTION:
  - Automatic renewal (certbot/acme.sh)
  - 30-day expiry warning alerts
  - Multiple renewal methods (HTTP-01, DNS-01)

DETECTION:
  - Certificate expiry monitoring (alert at 14 days)
  - Daily check of cert validity

IMMEDIATE FIX:
  - Manual renewal: certbot renew --force-renewal
  - Fallback to self-signed cert (allow dashboard access)
  - 90-day Let's Encrypt certs, renew at 30 days
```

---

#### Failure Mode 7: DDoS Attack on VPS-01

**Scenario:** Overlord IP targeted by DDoS attack

**Impact:**
- ❌ VPS-01 unreachable from internet
- ❌ Dashboard inaccessible
- ⚠️ Devices may be unable to report (if using public IP)
- ✅ Devices continue operating

**Mitigation:**
```yaml
PREVENTION:
  - VPS behind Cloudflare (DDoS protection)
  - Rate limiting on all endpoints
  - Fail2ban for repeated auth failures
  - VPN-only access for critical services

DETECTION:
  - Network traffic spike alerts
  - CPU spike from network processing
  - Connection count alerts

RESPONSE:
  - Enable Cloudflare "Under Attack" mode
  - Restrict access to VPN only
  - Change IP address if targeted
  - Contact VPS provider for null routing
```

---

#### Failure Mode 8: Backup Failure

**Scenario:** Automated backups fail silently, no recent backup exists

**Impact:**
- ⚠️ Data loss if VPS-01 fails
- ⚠️ Longer recovery time

**Mitigation:**
```yaml
PREVENTION:
  - Multiple backup destinations (S3, B2, local)
  - Backup verification (restore test monthly)
  - Immutable backups (append-only, cannot delete)

DETECTION:
  - Backup success/failure monitoring
  - Alert if backup age >24 hours
  - Backup size anomaly detection (too small = failed)

VERIFICATION:
  - Monthly disaster recovery drill (restore from backup)
  - Automated backup restore testing
  - Checksum verification of backup files
```

---

#### Failure Mode 9: Time Drift

**Scenario:** VPS-01 clock skews, causes metric timestamp issues

**Impact:**
- ⚠️ Metrics out of order
- ⚠️ Alert timing incorrect
- ⚠️ TLS certificate validation fails

**Mitigation:**
```yaml
PREVENTION:
  - NTP time synchronization (systemd-timesyncd)
  - Multiple NTP servers configured
  - Hardware clock sync

DETECTION:
  - Clock skew monitoring (alert if >30s drift)
  - NTP sync status check

IMMEDIATE FIX:
  - Force NTP sync: timedatectl set-ntp true
  - Restart time-sensitive services
```

---

#### Failure Mode 10: Malicious Access (Compromised Overlord)

**Scenario:** Attacker gains access to VPS-01

**Impact:**
- 🔴 **CRITICAL:** Entire fleet visibility compromised
- 🔴 Can view all device status, logs, metrics
- 🔴 Can modify configurations, inject malicious updates
- 🔴 Can disable alerts, hide their tracks

**Mitigation:**
```yaml
PREVENTION:
  - SSH key only (no password auth)
  - 2FA for all web interfaces
  - Firewall: whitelist IPs only
  - Intrusion detection (fail2ban, OSSEC)
  - Regular security updates
  - Audit logs for all actions

DETECTION:
  - Login anomaly detection
  - Unexpected process alerts
  - File integrity monitoring (AIDE)
  - Network connection monitoring

RESPONSE:
  - Isolate VPS-01 immediately
  - Revoke all API keys
  - Rotate all secrets
  - Forensic investigation
  - Restore from known-good backup
```

---

## PART 5: MONITORING THE MONITOR

**Problem:** If VPS-01 fails, who alerts you?

### External Monitoring (Independent)

```yaml
Service: UptimeRobot, Pingdom, or StatusCake
Cost: Free tier sufficient for small fleet

Checks:
  - HTTP check: https://overlord.example.com/health every 5 min
  - Ping check: VPS-01 IP address every 5 min
  - Port checks: 9090 (Prometheus), 3000 (Grafana), 8080 (Dashboard)

Alerts:
  - Email to on-call
  - SMS for critical services
  - Slack/Discord webhook

Expected Response Time: <5 minutes (faster than internal alerts)
```

### Dead Man's Switch

```yaml
Service: Dead Man's Snitch, Cronitor, or Healthchecks.io
Cost: $5-10/month

VPS-01 Heartbeat:
  - Cron job sends HTTP ping every 5 minutes
  - If ping missed → alert fires
  - Independent of VPS-01 monitoring stack

# Crontab on VPS-01
*/5 * * * * curl -m 30 https://nosnch.in/abc123def456 || true

Alert:
  - Email, SMS, phone call
  - Escalation: 15 min no heartbeat → page on-call
```

### Self-Monitoring Stack

```yaml
# VPS-01 monitors itself
Node Exporter:
  - CPU, memory, disk, network metrics
  - Prometheus scrapes node_exporter

Container Monitoring:
  - cAdvisor for Docker container metrics
  - Per-container CPU, memory, disk I/O

Service Health Checks:
  - Prometheus: http://localhost:9090/-/healthy
  - Grafana: http://localhost:3000/api/health
  - PostgreSQL: pg_isready
  - All checked every 60s

Alerts:
  - CPU >80% for 5 min
  - Memory >80% for 5 min
  - Disk >90% full
  - Any service down for >2 min
  - Network errors increasing
```

---

## PART 6: BACKUP AND DISASTER RECOVERY

### Backup Strategy

```yaml
DAILY Backups (Automated):
  PostgreSQL:
    - pg_dump full database
    - Compressed with gzip
    - Uploaded to S3/B2
    - Retention: 30 days

  Prometheus:
    - Snapshot TSDB
    - Upload to object storage
    - Retention: 7 days (metrics less critical)

  Grafana:
    - Export all dashboards (JSON)
    - Backup SQLite database
    - Retention: 30 days

  Configuration:
    - Tar all /opt/overlord config files
    - Git commit to backup repo
    - Retention: Forever (Git history)

WEEKLY Backups:
  - Full system snapshot (if VPS provider supports)
  - Offline backup to local storage
  - Verified restore test

MONTHLY:
  - Disaster recovery drill (full restore)
  - Backup to separate geographic region
  - Archive to cold storage
```

### Backup Automation Script

```bash
#!/bin/bash
# /opt/overlord/scripts/backup.sh

set -euo pipefail

BACKUP_DIR="/opt/overlord/backups"
DATE=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="s3://metrica-fleet-backups"

# PostgreSQL backup
echo "Backing up PostgreSQL..."
docker exec postgres pg_dump -U metrica metrica_fleet | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Grafana backup
echo "Backing up Grafana..."
docker exec grafana grafana-cli admin export-dashboards --path=/tmp/dashboards
docker cp grafana:/tmp/dashboards "$BACKUP_DIR/grafana_$DATE"

# Prometheus snapshot
echo "Backing up Prometheus..."
curl -XPOST http://localhost:9090/api/v1/admin/tsdb/snapshot
# Copy snapshot to backup dir

# Configuration backup
echo "Backing up configuration..."
tar czf "$BACKUP_DIR/config_$DATE.tar.gz" /opt/overlord/{prometheus,grafana,loki,nginx}

# Upload to S3
echo "Uploading to S3..."
aws s3 sync "$BACKUP_DIR" "$S3_BUCKET" --storage-class STANDARD_IA

# Cleanup old local backups (>7 days)
find "$BACKUP_DIR" -type f -mtime +7 -delete

echo "Backup completed: $DATE"

# Send success metric to external monitoring
curl -m 30 "https://healthchecks.io/ping/backup-success"
```

### Disaster Recovery Procedure

**Scenario:** VPS-01 completely destroyed, need to rebuild from scratch

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 24 hours

```yaml
Step 1: Provision New VPS (30 min)
  - Deploy new VPS with same specs
  - Configure network, firewall, SSH
  - Install Docker + Docker Compose

Step 2: Restore Configuration (30 min)
  - Clone configuration repository
  - Restore /opt/overlord structure
  - Update DNS to point to new IP
  - Generate new SSL certificates

Step 3: Restore Data (2 hours)
  - Download latest backups from S3
  - Restore PostgreSQL: psql < backup.sql
  - Restore Grafana dashboards
  - Restore Prometheus (or let it rebuild from devices)

Step 4: Start Services (30 min)
  - docker-compose up -d
  - Verify all services healthy
  - Check Prometheus targets
  - Verify Grafana dashboards loading

Step 5: Verify Fleet Connectivity (30 min)
  - Devices start reporting to new VPS
  - Metrics flowing into Prometheus
  - Logs arriving in Loki
  - Dashboard shows all devices

Step 6: Update Fleet (30 min)
  - Update device configs with new VPS IP (if needed)
  - Git commit to update Prometheus endpoints
  - Devices converge to new config automatically

Total Time: 4 hours (can be parallelized to 2 hours with team)
```

### Failover to VPS-02 (Backup Overlord)

**If VPS-02 configured as hot standby:**

```yaml
Failover Process (Automatic):
  1. External monitoring detects VPS-01 down
  2. DNS failover: overlord.example.com → VPS-02 IP
     (using health-checked DNS or manual change)
  3. VPS-02 already running monitoring stack
  4. VPS-02 database replicating from VPS-01 (streaming replication)
  5. Devices reconnect to VPS-02 within 5 minutes

Failover Time: 5-10 minutes
Data Loss: None (if replication working)
```

---

## PART 7: NETWORK ARCHITECTURE

### Fleet Network Topology

```
                    INTERNET
                       │
                       │
         ┌─────────────┴─────────────┐
         │                           │
    ┌────▼─────┐              ┌─────▼────┐
    │  VPS-01  │              │ GitHub   │
    │ Overlord │              │ (Git)    │
    └────┬─────┘              └──────────┘
         │                          ▲
         │ Tailscale VPN            │
         │ or Public IPs            │
         │                          │
    ┌────┴─────────────────────────┴──────┐
    │                                      │
    │  FLEET DEVICES (50+)                 │
    │                                      │
    │  ┌──────┐  ┌──────┐  ┌──────┐      │
    │  │ Pi-01│  │ Pi-02│  │ Pi-03│ ...  │
    │  │Camera│  │Sensor│  │ Gate │      │
    │  └──┬───┘  └──┬───┘  └──┬───┘      │
    │     │         │         │           │
    └─────┼─────────┼─────────┼───────────┘
          │         │         │
      ┌───▼─────────▼─────────▼────┐
      │   Local Network / Internet │
      └────────────────────────────┘
```

### Communication Patterns

```yaml
Devices → VPS-01:
  Metrics (Prometheus):
    - VPS-01 scrapes device :9100/metrics (node_exporter)
    - VPS-01 scrapes device :19999/api/v1/allmetrics (Netdata)
    - Protocol: HTTP (or HTTPS)
    - Frequency: Every 15s
    - Direction: PULL (VPS-01 initiates)

  Logs (Loki):
    - Device Promtail pushes to VPS-01 :3100
    - Protocol: HTTP
    - Frequency: Real-time (batched every 10s)
    - Direction: PUSH (device initiates)

  Status Updates (Database):
    - Device agent POST to VPS-01 :8080/api/status
    - Protocol: HTTPS
    - Frequency: Every 60s
    - Direction: PUSH (device initiates)

Devices → GitHub:
  Config Fetch:
    - Device pulls raw.githubusercontent.com
    - Protocol: HTTPS
    - Frequency: Every 60s (check for updates)
    - Direction: PULL (device initiates)

VPS-01 → External:
  Alerts:
    - Email via SMTP (Sendgrid, Mailgun)
    - Webhooks to Slack/Discord
    - PagerDuty API calls
    - Direction: PUSH (VPS-01 initiates)

  Heartbeat:
    - VPS-01 pings Dead Man's Snitch
    - Protocol: HTTPS
    - Frequency: Every 5 min
```

### Firewall Rules (ufw)

```bash
# VPS-01 Firewall Configuration

# Default policies
ufw default deny incoming
ufw default allow outgoing

# SSH (from specific IPs only)
ufw allow from 203.0.113.0/24 to any port 22 proto tcp comment 'SSH from office'

# HTTPS (dashboard, public access)
ufw allow 443/tcp comment 'HTTPS for dashboard'

# HTTP (redirect to HTTPS)
ufw allow 80/tcp comment 'HTTP redirect'

# Prometheus scrape (from devices only, if using public IPs)
# Better: use Tailscale VPN, no firewall rules needed

# Enable firewall
ufw enable
```

### Tailscale VPN Setup (Recommended)

**Why Tailscale:**
- Encrypted mesh network
- No firewall configuration needed
- Private IPs for all devices
- NAT traversal (works behind firewalls)
- Free for up to 100 devices

```bash
# Install Tailscale on VPS-01
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --advertise-routes=10.0.0.0/24

# Install Tailscale on each Pi device
# (handled by device provisioning script)

# Result: All devices communicate over 100.x.y.z private IPs
# VPS-01: 100.64.0.1
# Pi-01: 100.64.0.2
# Pi-02: 100.64.0.3
# etc.
```

---

## PART 8: SECURITY HARDENING

### Security Checklist

```yaml
Operating System:
  - [ ] Automatic security updates enabled
  - [ ] SSH key authentication only (no passwords)
  - [ ] SSH on non-standard port (optional)
  - [ ] Fail2ban installed and configured
  - [ ] Root login disabled
  - [ ] Sudo requires password
  - [ ] Firewall (ufw) enabled with minimal rules

Docker:
  - [ ] Non-root containers where possible
  - [ ] Resource limits on all containers
  - [ ] No privileged containers
  - [ ] Read-only filesystem where possible
  - [ ] Secrets via environment variables or files (not in images)
  - [ ] Regular image updates (Dependabot)

Web Services:
  - [ ] All services behind SSL/TLS
  - [ ] Strong passwords (20+ chars random)
  - [ ] 2FA enabled on Grafana, Gitea
  - [ ] Rate limiting on API endpoints
  - [ ] CORS properly configured
  - [ ] Security headers (HSTS, CSP, etc.)

Network:
  - [ ] VPN for all fleet communication (Tailscale)
  - [ ] Public IPs only for HTTPS dashboard
  - [ ] DDoS protection (Cloudflare)
  - [ ] No unnecessary ports exposed

Secrets:
  - [ ] All passwords in environment variables
  - [ ] .env file not in Git
  - [ ] Secrets rotation schedule (90 days)
  - [ ] API keys have minimum required permissions
  - [ ] Database passwords 32+ chars

Monitoring:
  - [ ] Audit logs for all admin actions
  - [ ] Login attempt monitoring
  - [ ] File integrity monitoring (AIDE)
  - [ ] Intrusion detection alerts
```

---

## PART 9: IMPLEMENTATION ROADMAP

### Phase 0: VPS Provisioning (Week 1)

**Tasks:**
- [ ] Choose VPS provider (Hetzner recommended for ARM)
- [ ] Provision VPS-01 (4 vCPU, 8 GB RAM, 200 GB SSD)
- [ ] Set up SSH keys
- [ ] Configure firewall (ufw)
- [ ] Install Docker + Docker Compose
- [ ] Set up automatic security updates
- [ ] Configure DNS (overlord.example.com → VPS IP)

**Deliverable:** Secure, accessible VPS ready for service deployment

---

### Phase 1: Core Monitoring Stack (Week 2)

**Tasks:**
- [ ] Deploy Prometheus
- [ ] Deploy Grafana
- [ ] Deploy Loki
- [ ] Configure SSL with Let's Encrypt
- [ ] Create first test dashboard
- [ ] Test metrics ingestion from one Pi device

**Deliverable:** Working monitoring stack, visible in Grafana

**Verification:**
```bash
curl https://overlord.example.com/grafana/api/health  # HTTP 200
curl http://localhost:9090/-/healthy  # Prometheus healthy
```

---

### Phase 2: Database and Dashboard (Week 3)

**Tasks:**
- [ ] Deploy PostgreSQL
- [ ] Create metrica_fleet database schema
- [ ] Build fleet dashboard (React/Vue)
- [ ] Deploy dashboard container
- [ ] Configure Nginx reverse proxy
- [ ] Test device status reporting

**Deliverable:** Web UI showing fleet status

**Verification:**
- [ ] Dashboard loads at https://overlord.example.com
- [ ] Can see device list
- [ ] Device status updates in real-time

---

### Phase 3: Git Mirror (Week 4)

**Tasks:**
- [ ] Deploy Gitea
- [ ] Configure Gitea with PostgreSQL
- [ ] Mirror GitHub repository
- [ ] Set up automatic sync (GitHub → Gitea every 60s)
- [ ] Test device failover to Gitea

**Deliverable:** Redundant Git repository

**Verification:**
- [ ] Gitea accessible at https://overlord.example.com/git
- [ ] Repository syncing from GitHub
- [ ] Device can fetch from Gitea when GitHub unavailable

---

### Phase 4: Alerting (Week 5)

**Tasks:**
- [ ] Deploy Alertmanager
- [ ] Configure alert rules in Prometheus
- [ ] Set up email notifications (Sendgrid/Mailgun)
- [ ] Set up Slack/Discord webhooks
- [ ] Configure PagerDuty (if using)
- [ ] Test all alert channels

**Deliverable:** Alerts firing and routing correctly

**Verification:**
- [ ] Test alert fires correctly
- [ ] Email received within 3 minutes
- [ ] Slack message received
- [ ] PagerDuty page sent (if configured)

---

### Phase 5: External Monitoring (Week 5)

**Tasks:**
- [ ] Set up UptimeRobot checks
- [ ] Configure Dead Man's Snitch heartbeat
- [ ] Set up backup VPS-02 (optional)
- [ ] Test failover procedures

**Deliverable:** Independent monitoring of Overlord

**Verification:**
- [ ] VPS-01 shutdown → external alert fires within 5 min
- [ ] VPS-01 restored → external alert clears

---

### Phase 6: Backup System (Week 6)

**Tasks:**
- [ ] Create backup script
- [ ] Set up S3/B2 bucket
- [ ] Configure daily cron job
- [ ] Test backup restore
- [ ] Document disaster recovery procedure

**Deliverable:** Automated backup system

**Verification:**
- [ ] Backup runs daily without errors
- [ ] Backup uploaded to S3
- [ ] Restore from backup successful (tested)

---

### Phase 7: Security Hardening (Week 7)

**Tasks:**
- [ ] Install Fail2ban
- [ ] Configure intrusion detection
- [ ] Set up file integrity monitoring
- [ ] Enable 2FA on all web interfaces
- [ ] Security audit and penetration test
- [ ] Rotate all default passwords

**Deliverable:** Hardened, secure Overlord

**Verification:**
- [ ] Security scan passes (no critical vulnerabilities)
- [ ] 2FA working on Grafana, Gitea
- [ ] Intrusion detection alerts working

---

### Phase 8: Tailscale VPN (Week 8)

**Tasks:**
- [ ] Install Tailscale on VPS-01
- [ ] Install Tailscale on all Pi devices
- [ ] Configure Prometheus to use Tailscale IPs
- [ ] Test encrypted communication
- [ ] Remove public IP firewall rules

**Deliverable:** Secure VPN mesh network

**Verification:**
- [ ] All devices reachable via 100.x.y.z IPs
- [ ] Prometheus scraping over Tailscale
- [ ] No unencrypted traffic between devices

---

### Phase 9: Production Testing (Week 9-10)

**Tasks:**
- [ ] Chaos testing (kill services, simulate failures)
- [ ] Load testing (simulate 100 devices)
- [ ] Disaster recovery drill (restore from backup)
- [ ] Documentation review
- [ ] Runbook creation

**Deliverable:** Production-ready Overlord

**Verification:**
- [ ] All chaos tests passed
- [ ] Load test: 100 devices, <5s query time
- [ ] Disaster recovery: <4 hour RTO

---

### Phase 10: Fleet Integration (Week 11+)

**Tasks:**
- [ ] Update all devices to report to VPS-01
- [ ] Configure Prometheus scrape targets
- [ ] Set up Grafana dashboards for all device types
- [ ] Enable alerting for fleet
- [ ] Monitor for 2 weeks

**Deliverable:** Full fleet managed by Overlord

**Verification:**
- [ ] All 50+ devices reporting
- [ ] Metrics visible for all devices
- [ ] Alerts firing correctly
- [ ] Dashboard shows full fleet health

---

## PART 10: OPERATIONAL PROCEDURES

### Daily Operations

```yaml
Morning Check (5 min):
  - Check dashboard: all devices green?
  - Review overnight alerts
  - Check VPS-01 resource usage (CPU, memory, disk)
  - Verify backup ran successfully

Weekly Tasks (30 min):
  - Review Grafana dashboards for anomalies
  - Check disk usage trends
  - Review and acknowledge handled alerts
  - Update runbooks with new learnings

Monthly Tasks (2 hours):
  - Review monthly uptime report
  - Disaster recovery drill (restore from backup)
  - Security updates review
  - Capacity planning (will we outgrow VPS?)
```

### Incident Response

**P1 (Critical): VPS-01 Down**

```
1. Receive external alert (UptimeRobot, Dead Man's Snitch)
2. Attempt to SSH to VPS-01
3. If unreachable:
   - Check VPS provider status page
   - Attempt reboot via provider control panel
   - If still down: initiate disaster recovery
4. If reachable:
   - Check Docker: docker ps -a
   - Check logs: docker-compose logs
   - Restart failed services
5. Post-incident: Root cause analysis, update runbooks
```

**P2 (High): Service Down (Prometheus, Grafana, etc.)**

```
1. Receive alert (Prometheus monitoring itself)
2. SSH to VPS-01
3. Check service: docker ps | grep prometheus
4. Check logs: docker logs prometheus
5. Restart if needed: docker-compose restart prometheus
6. Verify: curl http://localhost:9090/-/healthy
7. Post-incident: Log to incident tracker
```

**P3 (Medium): Disk Space Low**

```
1. Receive alert (disk >80% full)
2. SSH to VPS-01
3. Check usage: df -h
4. Identify large directories: du -sh /var/lib/docker/volumes/*
5. Clean up:
   - Old Docker images: docker image prune -a
   - Old Prometheus blocks: reduce retention
   - Old logs: journalctl --vacuum-time=7d
6. If still low: upgrade disk size
```

---

## PART 11: COST ANALYSIS

### Monthly Operating Costs

```yaml
VPS-01 (Primary):
  Provider: Hetzner
  Instance: CPX31 (4 vCPU, 8 GB RAM, 160 GB SSD)
  Cost: €11.90/month (~$13 USD)

VPS-02 (Backup, optional):
  Provider: Hetzner (different datacenter)
  Instance: CPX21 (3 vCPU, 4 GB RAM, 80 GB SSD)
  Cost: €7.90/month (~$9 USD)

Storage (Backups):
  Provider: Backblaze B2
  Storage: 100 GB @ $0.005/GB = $0.50
  Egress: 10 GB/month @ $0.01/GB = $0.10
  Cost: $0.60/month

DNS:
  Provider: Cloudflare (free tier)
  Cost: $0

SSL Certificates:
  Provider: Let's Encrypt (free)
  Cost: $0

External Monitoring:
  Provider: UptimeRobot (free tier: 50 monitors)
  Cost: $0

  Provider: Dead Man's Snitch
  Cost: $5/month (20 snitches)

Email (Alerts):
  Provider: Sendgrid (free tier: 100 emails/day)
  Cost: $0

Total Monthly Cost:
  - Minimal setup: $13 (VPS-01 only)
  - Recommended setup: $27 (VPS-01 + VPS-02 + monitoring)
  - Annual cost: ~$324/year

Cost per device: $0.54/month (for 50 devices)
```

### 3-Year Total Cost of Ownership

```yaml
Hardware: $0 (VPS, no upfront cost)
Software: $0 (all open source)
VPS Hosting: $972 (3 years @ $27/month)
Labor (setup): $2,000 (40 hours @ $50/hour, one-time)
Labor (maintenance): $1,800 (1 hour/week @ $50/hour × 3 years)

Total 3-Year TCO: $4,772
Cost per device (50 devices): $95.44
Cost per device per month: $2.65
```

**Comparison to Managed Services:**

| Solution | Monthly Cost | 3-Year Cost |
|----------|--------------|-------------|
| **Self-Hosted Overlord** | $27 | $972 |
| Datadog (50 hosts) | $750 | $27,000 |
| New Relic (50 hosts) | $600 | $21,600 |
| Grafana Cloud | $300 | $10,800 |

**Savings: $20,000+ over 3 years**

---

## PART 12: ACCEPTANCE CRITERIA

### Before Declaring VPS-01 "Production Ready"

**All items must be ✓:**

#### Infrastructure
- [ ] VPS-01 deployed and accessible
- [ ] All Docker services running
- [ ] SSL certificates valid
- [ ] DNS resolving correctly
- [ ] Firewall configured correctly
- [ ] Automatic security updates enabled

#### Monitoring
- [ ] Prometheus scraping all devices
- [ ] Grafana dashboards created
- [ ] Loki receiving logs from devices
- [ ] Alertmanager routing alerts correctly
- [ ] External monitoring configured (UptimeRobot)
- [ ] Dead Man's Switch active

#### Database
- [ ] PostgreSQL running and healthy
- [ ] Database schema created
- [ ] Devices reporting status
- [ ] Dashboard showing device list

#### Backup
- [ ] Daily backups running automatically
- [ ] Backups uploading to S3/B2
- [ ] Disaster recovery procedure tested
- [ ] Restore from backup successful (verified)

#### Security
- [ ] 2FA enabled on all web interfaces
- [ ] SSH key authentication only
- [ ] Fail2ban installed and active
- [ ] No secrets in Git repository
- [ ] Security scan passed

#### Reliability
- [ ] VPS-01 uptime >99.9% for 30 days
- [ ] All services auto-restart on failure
- [ ] Chaos tests passed (service restarts)
- [ ] Disaster recovery drill passed (<4 hour RTO)

#### Performance
- [ ] Dashboard loads in <2 seconds
- [ ] Prometheus query time <5 seconds
- [ ] Grafana dashboard refresh <3 seconds
- [ ] CPU usage <50% average
- [ ] Memory usage <80% average
- [ ] Disk usage <70%

#### Documentation
- [ ] Architecture document complete
- [ ] Runbooks for all failure modes
- [ ] Disaster recovery procedure documented
- [ ] Backup/restore procedure documented
- [ ] Operational procedures documented

---

## CONCLUSION

**VPS-01 "Overlord" is the central nervous system of your fleet.**

### Key Takeaways

1. **Centralized Observability** - All metrics, logs, and status in one place
2. **Fleet Independence** - Devices operate normally even if Overlord fails
3. **Cost Effective** - $27/month for 50+ devices ($0.54/device)
4. **Disaster Recoverable** - 4-hour RTO with automated backups
5. **Scalable** - Can grow from 50 to 500 devices with vertical scaling

### Critical Success Factors

✅ **Build external monitoring first** - VPS-01 must be monitored independently
✅ **Test disaster recovery** - Regular drills ensure you can recover
✅ **Automate backups** - No manual intervention for daily backups
✅ **Harden security** - VPS-01 is a high-value target
✅ **Document everything** - Future you will thank present you

### The Overlord's Promise

**IF** you build VPS-01 according to this architecture:
- You WILL have full visibility into your fleet
- You WILL be alerted within 3 minutes of any issue
- You WILL be able to recover from total VPS failure in <4 hours
- You WILL save $20,000+ vs managed monitoring services
- You WILL sleep better knowing the fleet is monitored

**Build the Overlord with the same rigor as the fleet devices.**

Every service must be monitored.
Every failure mode must be tested.
Every backup must be verified.

The fleet depends on the Overlord.
The Overlord depends on you building it right.

---

**Next Steps:**

1. Review this architecture document
2. Provision VPS-01 (Week 1)
3. Deploy monitoring stack (Week 2)
4. Integrate first Pi device (Week 3)
5. Scale to full fleet (Week 11+)

**Document Version:** 1.0
**Last Updated:** 2025-11-10
**Next Review:** After Phase 1 deployment
**Status:** Ready for implementation
