# VPS-01 Overlord Implementation Checklist
**Zero-Defect Deployment Guide**

**Document Version:** 1.0
**Date:** 2025-11-10
**Purpose:** Step-by-step verified deployment of VPS-01 Overlord
**Target:** Production-ready central monitoring server for 50+ device fleet

---

## THE GOLDEN RULE

**🚨 Every checkbox must be ✓ and verified before moving to next phase**

No shortcuts. No assumptions. No "we'll fix it later."

**If VPS-01 fails, you are blind. Build it right.**

---

## PHASE 0: VPS PROVISIONING (Day 1)

### Step 1: Choose VPS Provider

**Criteria:**
- ARM64 support (cost savings) OR AMD64 (compatibility)
- Good network reliability (99.9%+ SLA)
- Snapshot/backup support
- Hourly billing (flexibility)
- DDoS protection available

**Recommended Providers:**

| Provider | Specs | Monthly Cost | Notes |
|----------|-------|--------------|-------|
| **Hetzner** | CPX31 (4 vCPU, 8 GB, 160 GB) | $13 | Best value, ARM64 available |
| DigitalOcean | 4 vCPU, 8 GB, 160 GB | $48 | Easy UI, good docs |
| Vultr | 4 vCPU, 8 GB, 160 GB | $24 | Global locations |
| Linode | 4 vCPU, 8 GB, 160 GB | $36 | Reliable, good support |

**Decision:**
- [ ] Provider selected: ________________
- [ ] Account created and verified
- [ ] Billing configured

---

### Step 2: Deploy VPS-01

```bash
# Specifications
Region: ________________ (closest to fleet)
OS: Ubuntu 24.04 LTS Server (ARM64 or AMD64)
Hostname: overlord
FQDN: overlord.example.com
```

**Checklist:**
- [ ] VPS created and running
- [ ] Public IPv4 address assigned: ________________
- [ ] (Optional) IPv6 address assigned: ________________
- [ ] SSH access working with password (temporary)
- [ ] DNS A record created: overlord.example.com → IPv4
- [ ] DNS AAAA record created (if IPv6): overlord.example.com → IPv6
- [ ] Hostname set: `hostnamectl set-hostname overlord`

**Verification:**
```bash
# From your workstation:
ping overlord.example.com  # Should respond
ssh root@overlord.example.com  # Should connect
```

---

### Step 3: Initial Security Hardening

**Create non-root user:**
```bash
# On VPS-01:
adduser metrica
usermod -aG sudo metrica
```

**Set up SSH key authentication:**
```bash
# On your workstation:
ssh-keygen -t ed25519 -C "overlord-access" -f ~/.ssh/overlord_ed25519

# Copy public key to VPS-01:
ssh-copy-id -i ~/.ssh/overlord_ed25519.pub metrica@overlord.example.com

# Test key-based login:
ssh -i ~/.ssh/overlord_ed25519 metrica@overlord.example.com
```

**Disable password authentication:**
```bash
# On VPS-01 (as root):
nano /etc/ssh/sshd_config

# Set these values:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no

# Restart SSH:
systemctl restart sshd
```

**Checklist:**
- [ ] User `metrica` created
- [ ] SSH key generated
- [ ] SSH key added to VPS-01
- [ ] Key-based login tested and working
- [ ] Password authentication disabled
- [ ] Root login disabled
- [ ] Can still SSH in with key (DO NOT lock yourself out!)

**Verification:**
```bash
# From workstation:
ssh -i ~/.ssh/overlord_ed25519 metrica@overlord.example.com
# Should work without password

ssh root@overlord.example.com
# Should be rejected
```

---

### Step 4: Configure Firewall

```bash
# On VPS-01:
sudo apt update
sudo apt install -y ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (CRITICAL: Do this first or you'll lock yourself out!)
sudo ufw allow 22/tcp comment 'SSH'

# Allow HTTP and HTTPS (for dashboard)
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

**Checklist:**
- [ ] ufw installed
- [ ] SSH port 22 allowed BEFORE enabling firewall
- [ ] HTTP/HTTPS ports allowed
- [ ] Firewall enabled
- [ ] Can still SSH after firewall enabled (verify!)

**Verification:**
```bash
sudo ufw status
# Status: active
# Should show ports 22, 80, 443 open
```

---

### Step 5: System Updates and Essential Packages

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
  curl \
  wget \
  git \
  vim \
  htop \
  tmux \
  net-tools \
  dnsutils \
  ca-certificates \
  gnupg \
  lsb-release \
  unattended-upgrades \
  fail2ban

# Configure automatic security updates
sudo dpkg-reconfigure --priority=low unattended-upgrades
# Select "Yes" to enable automatic updates
```

**Checklist:**
- [ ] System fully updated
- [ ] Essential packages installed
- [ ] Automatic security updates enabled
- [ ] Fail2ban installed (SSH protection)

**Verification:**
```bash
# Check for updates
sudo apt update && sudo apt list --upgradable
# Should show "All packages are up to date"

# Check fail2ban status
sudo systemctl status fail2ban
# Should be active and running
```

---

### Step 6: Install Docker and Docker Compose

```bash
# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group (no sudo needed for docker commands)
sudo usermod -aG docker metrica

# Log out and back in for group to take effect
exit
# SSH back in

# Test Docker
docker run hello-world
```

**Checklist:**
- [ ] Docker installed
- [ ] Docker Compose plugin installed
- [ ] User added to docker group
- [ ] Docker hello-world test passed
- [ ] Can run `docker ps` without sudo

**Verification:**
```bash
docker --version
# Docker version 24.0.x or higher

docker compose version
# Docker Compose version v2.x.x or higher

docker ps
# Should work without sudo
# Should show: CONTAINER ID   IMAGE   COMMAND   CREATED   STATUS   PORTS   NAMES
# (empty list is OK)
```

---

### Step 7: Create Directory Structure

```bash
# Create main directory
sudo mkdir -p /opt/overlord
sudo chown metrica:metrica /opt/overlord
cd /opt/overlord

# Create service directories
mkdir -p {prometheus,grafana,loki,alertmanager,nginx,postgres,gitea,dashboard}
mkdir -p {scripts,backups,logs}

# Create configuration subdirectories
mkdir -p prometheus/{rules,targets}
mkdir -p grafana/provisioning/{dashboards,datasources}
mkdir -p nginx/{conf.d,ssl}
```

**Checklist:**
- [ ] /opt/overlord directory created
- [ ] Ownership set to metrica user
- [ ] All subdirectories created

**Verification:**
```bash
ls -la /opt/overlord
# Should show all subdirectories
# Owner should be metrica:metrica
```

---

### Step 8: Configure NTP Time Synchronization

```bash
# Check current time
timedatectl

# Enable NTP
sudo timedatectl set-ntp true

# Check status
timedatectl status
```

**Checklist:**
- [ ] NTP enabled
- [ ] System clock synchronized
- [ ] Timezone correct

**Verification:**
```bash
timedatectl
# Should show:
# System clock synchronized: yes
# NTP service: active
```

---

## PHASE 0 COMPLETION CHECKLIST

**Before proceeding to Phase 1, verify ALL:**

- [ ] VPS provisioned and accessible
- [ ] SSH key authentication working
- [ ] Password authentication disabled
- [ ] Firewall configured and enabled
- [ ] System fully updated
- [ ] Automatic security updates enabled
- [ ] Fail2ban running
- [ ] Docker and Docker Compose installed
- [ ] Directory structure created
- [ ] NTP time synchronized
- [ ] DNS resolving correctly
- [ ] Can SSH in without issues
- [ ] User has sudo access
- [ ] User can run docker without sudo

**Phase 0 Duration:** 2-4 hours
**Next Phase:** Phase 1 - Core Monitoring Stack

---

## PHASE 1: CORE MONITORING STACK (Days 2-3)

### Step 1: Deploy Prometheus

**Create configuration:**
```bash
cd /opt/overlord/prometheus

# Create prometheus.yml
cat > prometheus.yml <<'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'metrica-fleet'
    overlord: 'vps-01'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# Load rules
rule_files:
  - "/etc/prometheus/rules/*.yml"

# Scrape configurations
scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # VPS-01 node_exporter (will install later)
  - job_name: 'vps-01'
    static_configs:
      - targets: ['localhost:9100']
        labels:
          instance: 'vps-01'
          role: 'overlord'

  # Fleet devices (will populate from file)
  - job_name: 'fleet-devices'
    file_sd_configs:
      - files:
        - '/etc/prometheus/targets/*.json'
        refresh_interval: 60s
EOF

# Create alert rules
mkdir -p rules
cat > rules/vps01.yml <<'EOF'
groups:
  - name: vps01_alerts
    interval: 30s
    rules:
      # VPS-01 down
      - alert: VPS01Down
        expr: up{job="vps-01"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "VPS-01 Overlord is down"
          description: "VPS-01 has been unreachable for 2 minutes"

      # High CPU
      - alert: HighCPU
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ $value }}%"

      # High memory
      - alert: HighMemory
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value }}%"

      # Disk space low
      - alert: DiskSpaceLow
        expr: (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Disk usage is {{ $value }}%"
EOF

# Create empty targets directory
mkdir -p targets
```

**Deploy Prometheus container:**
```bash
cd /opt/overlord

# Create minimal docker-compose.yml for now
cat > docker-compose.yml <<'EOF'
version: "3.8"

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: always
    user: "1000:1000"  # Run as metrica user
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=90d'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    networks:
      - monitoring

  # Node exporter for VPS-01 itself
  node_exporter:
    image: prom/node-exporter:latest
    container_name: node_exporter
    restart: always
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    ports:
      - "9100:9100"
    networks:
      - monitoring

volumes:
  prometheus_data:

networks:
  monitoring:
EOF

# Start Prometheus
docker compose up -d prometheus node_exporter

# Check logs
docker compose logs -f prometheus
# Press Ctrl+C to exit logs
```

**Checklist:**
- [ ] prometheus.yml created
- [ ] Alert rules created
- [ ] docker-compose.yml created
- [ ] Prometheus container running
- [ ] node_exporter container running
- [ ] No errors in logs

**Verification:**
```bash
# Check containers
docker ps
# Should show prometheus and node_exporter running

# Check Prometheus UI
curl http://localhost:9090/-/healthy
# Should return: "Prometheus is Healthy."

# Check targets
curl http://localhost:9090/api/v1/targets | jq
# Should show prometheus and vps-01 targets

# Access Prometheus UI from browser:
# http://overlord.example.com:9090
# (temporarily allow port 9090 in firewall if needed)
```

---

### Step 2: Deploy Grafana

**Create Grafana configuration:**
```bash
cd /opt/overlord/grafana

# Create datasource provisioning
mkdir -p provisioning/datasources
cat > provisioning/datasources/prometheus.yml <<'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
EOF

# Create dashboard provisioning
mkdir -p provisioning/dashboards
cat > provisioning/dashboards/default.yml <<'EOF'
apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF
```

**Add Grafana to docker-compose.yml:**
```bash
cd /opt/overlord

# Edit docker-compose.yml and add Grafana service
cat >> docker-compose.yml <<'EOF'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: always
    user: "1000:1000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_ROOT_URL=https://overlord.example.com/grafana
      - GF_SERVER_SERVE_FROM_SUB_PATH=true
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
    ports:
      - "3000:3000"
    networks:
      - monitoring
    depends_on:
      - prometheus
EOF

# Add grafana_data volume to volumes section (edit manually or append)
# volumes:
#   prometheus_data:
#   grafana_data:  # <-- add this
```

**Create .env file for secrets:**
```bash
cd /opt/overlord

# Generate strong password
GRAFANA_PASSWORD=$(openssl rand -base64 32)

# Create .env file
cat > .env <<EOF
# Grafana
GRAFANA_ADMIN_PASSWORD=${GRAFANA_PASSWORD}

# PostgreSQL (will use later)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
EOF

# Secure .env file
chmod 600 .env

# Print passwords (SAVE THESE!)
echo "=== SAVE THESE CREDENTIALS ==="
cat .env
echo "=============================="
```

**Deploy Grafana:**
```bash
docker compose up -d grafana

# Check logs
docker compose logs -f grafana
```

**Checklist:**
- [ ] Grafana datasource provisioning configured
- [ ] .env file created with strong passwords
- [ ] Credentials saved securely (password manager)
- [ ] Grafana container running
- [ ] No errors in logs

**Verification:**
```bash
# Check container
docker ps | grep grafana

# Check Grafana health
curl http://localhost:3000/api/health
# Should return: {"commit":"...","database":"ok","version":"..."}

# Login to Grafana
# Browser: http://overlord.example.com:3000
# Username: admin
# Password: (from .env file)

# In Grafana:
# 1. Go to Configuration → Data Sources
# 2. Should see "Prometheus" datasource configured
# 3. Click "Test" → should say "Data source is working"
```

---

### Step 3: Deploy Loki and Promtail

**Create Loki configuration:**
```bash
cd /opt/overlord/loki

cat > loki-config.yml <<'EOF'
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2024-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h  # 7 days
  retention_period: 720h  # 30 days

chunk_store_config:
  max_look_back_period: 720h  # 30 days

table_manager:
  retention_deletes_enabled: true
  retention_period: 720h  # 30 days
EOF
```

**Add Loki to docker-compose.yml:**
```bash
cd /opt/overlord

# Append Loki service
cat >> docker-compose.yml <<'EOF'

  loki:
    image: grafana/loki:latest
    container_name: loki
    restart: always
    user: "1000:1000"
    volumes:
      - ./loki:/etc/loki
      - loki_data:/loki
    command: -config.file=/etc/loki/loki-config.yml
    ports:
      - "3100:3100"
    networks:
      - monitoring
EOF

# Add loki_data volume
```

**Add Loki datasource to Grafana:**
```bash
cd /opt/overlord/grafana/provisioning/datasources

cat > loki.yml <<'EOF'
apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
EOF
```

**Deploy Loki:**
```bash
cd /opt/overlord
docker compose up -d loki

# Restart Grafana to pick up new datasource
docker compose restart grafana

# Check logs
docker compose logs -f loki
```

**Checklist:**
- [ ] Loki configuration created
- [ ] Loki container running
- [ ] Loki datasource added to Grafana
- [ ] No errors in logs

**Verification:**
```bash
# Check Loki health
curl http://localhost:3100/ready
# Should return: "ready"

# In Grafana:
# Configuration → Data Sources → Add Loki
# Should see Loki datasource
# Test connection → should work
```

---

### Step 4: Deploy Alertmanager

**Create Alertmanager configuration:**
```bash
cd /opt/overlord/alertmanager

cat > config.yml <<'EOF'
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical'
      continue: true
    - match:
        severity: warning
      receiver: 'warning'

receivers:
  - name: 'default'
    # Placeholder - will configure email/Slack later

  - name: 'critical'
    # Placeholder for critical alerts

  - name: 'warning'
    # Placeholder for warnings

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
EOF
```

**Add Alertmanager to docker-compose.yml:**
```bash
cd /opt/overlord

cat >> docker-compose.yml <<'EOF'

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    restart: always
    user: "1000:1000"
    volumes:
      - ./alertmanager:/etc/alertmanager
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/config.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    networks:
      - monitoring
EOF

# Add alertmanager_data volume
```

**Deploy Alertmanager:**
```bash
cd /opt/overlord
docker compose up -d alertmanager

# Check logs
docker compose logs -f alertmanager
```

**Checklist:**
- [ ] Alertmanager configuration created
- [ ] Alertmanager container running
- [ ] No errors in logs

**Verification:**
```bash
# Check Alertmanager health
curl http://localhost:9093/-/healthy
# Should return: "Healthy"

# Check Prometheus can reach Alertmanager
curl http://localhost:9090/api/v1/alertmanagers | jq
# Should show alertmanager in targets

# Browser: http://overlord.example.com:9093
# Should see Alertmanager UI
```

---

### Step 5: Configure SSL with Let's Encrypt

**Install certbot:**
```bash
sudo apt install -y certbot
```

**Get SSL certificate:**
```bash
# Temporarily allow HTTP for Let's Encrypt challenge
sudo ufw allow 80/tcp

# Get certificate (replace with your domain)
sudo certbot certonly --standalone \
  -d overlord.example.com \
  --email your-email@example.com \
  --agree-tos \
  --non-interactive

# Certificates saved to:
# /etc/letsencrypt/live/overlord.example.com/fullchain.pem
# /etc/letsencrypt/live/overlord.example.com/privkey.pem

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/overlord.example.com/fullchain.pem /opt/overlord/nginx/ssl/
sudo cp /etc/letsencrypt/live/overlord.example.com/privkey.pem /opt/overlord/nginx/ssl/
sudo chown -R metrica:metrica /opt/overlord/nginx/ssl

# Set up automatic renewal
sudo crontab -e
# Add line:
# 0 3 * * * certbot renew --quiet && systemctl reload nginx
```

**Checklist:**
- [ ] certbot installed
- [ ] SSL certificate obtained
- [ ] Certificates copied to /opt/overlord/nginx/ssl/
- [ ] Auto-renewal configured

**Verification:**
```bash
# Check certificate
sudo certbot certificates

# Should show certificate valid for 90 days
```

---

### Step 6: Deploy Nginx Reverse Proxy

**Create Nginx configuration:**
```bash
cd /opt/overlord/nginx

cat > nginx.conf <<'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    keepalive_timeout 65;
    gzip on;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=api:10m rate=50r/s;

    # HTTP → HTTPS redirect
    server {
        listen 80;
        server_name overlord.example.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS
    server {
        listen 443 ssl http2;
        server_name overlord.example.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Grafana
        location /grafana/ {
            proxy_pass http://grafana:3000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            limit_req zone=general burst=20 nodelay;
        }

        # Prometheus (optional, can keep internal only)
        # location /prometheus/ {
        #     proxy_pass http://prometheus:9090/;
        # }

        # Default: Dashboard (will add later)
        location / {
            return 200 "VPS-01 Overlord - Operational\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF
```

**Add Nginx to docker-compose.yml:**
```bash
cd /opt/overlord

cat >> docker-compose.yml <<'EOF'

  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: always
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    ports:
      - "80:80"
      - "443:443"
    networks:
      - monitoring
    depends_on:
      - grafana
EOF
```

**Deploy Nginx:**
```bash
cd /opt/overlord
docker compose up -d nginx

# Check logs
docker compose logs -f nginx
```

**Checklist:**
- [ ] Nginx configuration created
- [ ] SSL certificates in place
- [ ] Nginx container running
- [ ] No errors in logs

**Verification:**
```bash
# Check Nginx
docker ps | grep nginx

# Test HTTPS
curl -I https://overlord.example.com
# Should return HTTP 200

# Test Grafana through Nginx
curl -I https://overlord.example.com/grafana/
# Should return HTTP 200 or 302

# Browser: https://overlord.example.com/grafana
# Should load Grafana with valid SSL certificate
```

---

## PHASE 1 COMPLETION CHECKLIST

**Before proceeding to Phase 2, verify ALL:**

- [ ] Prometheus running and scraping targets
- [ ] Grafana accessible at https://overlord.example.com/grafana
- [ ] Grafana can query Prometheus data
- [ ] Loki running and accessible
- [ ] Alertmanager running
- [ ] Nginx reverse proxy working
- [ ] SSL certificate valid
- [ ] HTTP redirects to HTTPS
- [ ] All containers auto-restart on reboot
- [ ] No errors in any container logs

**Test:**
```bash
# Reboot VPS
sudo reboot

# Wait 2 minutes, then verify all services came back
ssh metrica@overlord.example.com
docker ps
# All containers should be running

# Browser: https://overlord.example.com/grafana
# Should load without errors
```

**Phase 1 Duration:** 4-8 hours
**Next Phase:** Phase 2 - Database and Dashboard

---

## PHASE 2: DATABASE AND DASHBOARD (Days 4-5)

### Step 1: Deploy PostgreSQL

**Add PostgreSQL to docker-compose.yml:**
```bash
cd /opt/overlord

cat >> docker-compose.yml <<'EOF'

  postgres:
    image: postgres:16-alpine
    container_name: postgres
    restart: always
    environment:
      - POSTGRES_DB=metrica_fleet
      - POSTGRES_USER=metrica
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "127.0.0.1:5432:5432"  # Only accessible from localhost
    networks:
      - database
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U metrica -d metrica_fleet"]
      interval: 10s
      timeout: 5s
      retries: 5
EOF

# Add database network
# networks:
#   monitoring:
#   database:  # <-- add this
```

**Create database schema:**
```bash
cd /opt/overlord/postgres

cat > init.sql <<'EOF'
-- Metrica Fleet Database Schema

-- Devices table
CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(255) PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL,
    role VARCHAR(100) NOT NULL,
    git_commit VARCHAR(64),
    git_branch VARCHAR(100) DEFAULT 'main',
    status VARCHAR(50) DEFAULT 'unknown',  -- healthy, degraded, safe_mode, offline
    last_seen TIMESTAMP WITH TIME ZONE,
    last_update TIMESTAMP WITH TIME ZONE,
    last_update_result VARCHAR(50),  -- success, failure, rollback
    current_error TEXT,
    agent_version VARCHAR(50),
    uptime_seconds BIGINT,
    ip_address INET,
    tailscale_ip INET,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Deployment history
CREATE TABLE IF NOT EXISTS deployment_history (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) REFERENCES devices(device_id),
    git_commit VARCHAR(64) NOT NULL,
    deployed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    result VARCHAR(50),  -- success, failure, rollback
    duration_seconds INTEGER,
    error_message TEXT
);

-- Fleet-wide configuration
CREATE TABLE IF NOT EXISTS fleet_config (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default config
INSERT INTO fleet_config (key, value) VALUES
    ('emergency_stop', 'false'),
    ('canary_device_id', NULL),
    ('rollout_percentage', '100'),
    ('update_interval_seconds', '60')
ON CONFLICT (key) DO NOTHING;

-- Indexes
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_role ON devices(role);
CREATE INDEX idx_devices_last_seen ON devices(last_seen);
CREATE INDEX idx_deployment_device ON deployment_history(device_id);
CREATE INDEX idx_deployment_timestamp ON deployment_history(deployed_at);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
EOF
```

**Deploy PostgreSQL:**
```bash
cd /opt/overlord
docker compose up -d postgres

# Wait for PostgreSQL to be ready
sleep 10

# Check logs
docker compose logs -f postgres
```

**Checklist:**
- [ ] PostgreSQL password in .env file
- [ ] init.sql schema created
- [ ] PostgreSQL container running
- [ ] Health check passing
- [ ] No errors in logs

**Verification:**
```bash
# Check container
docker ps | grep postgres

# Check health
docker exec postgres pg_isready -U metrica -d metrica_fleet
# Should return: "accepting connections"

# Connect to database
docker exec -it postgres psql -U metrica -d metrica_fleet

# In psql:
\dt  # List tables (should show devices, deployment_history, fleet_config)
\q   # Quit
```

---

## PHASE 2 COMPLETION CHECKLIST

**Before proceeding, verify:**
- [ ] PostgreSQL running and healthy
- [ ] Database schema created
- [ ] Can connect to database
- [ ] All tables created

**Phase 2 Duration:** 2-4 hours
**Total Time So Far:** ~12-16 hours over 4-5 days

---

## SUMMARY: VPS-01 DEPLOYMENT STATUS

After completing Phase 0-2, you have:

✅ **Infrastructure:**
- Secure VPS with hardened SSH
- Firewall configured
- Docker environment ready
- SSL certificates in place

✅ **Monitoring Stack:**
- Prometheus collecting metrics
- Grafana visualization
- Loki log aggregation
- Alertmanager for alerts
- All accessible via HTTPS

✅ **Database:**
- PostgreSQL for device status
- Schema ready for fleet integration

✅ **Security:**
- SSH key authentication only
- Automatic security updates
- Fail2ban protection
- SSL/TLS encryption
- Secrets in .env file (not in Git)

**Next Steps:**
- Phase 3: Git mirror (Gitea)
- Phase 4: Alerting configuration
- Phase 5: External monitoring
- Phase 6: Backup automation
- Phase 7-8: Security and VPN
- Phase 9-10: Testing and fleet integration

**Estimated Time to Production:**
- Phases 0-2 complete: 12-16 hours
- Phases 3-10 remaining: 20-30 hours
- **Total: 32-46 hours (~1-2 weeks part-time)**

---

**Remember:**
Every checkbox exists for a reason.
Every verification prevents a production failure.
Build VPS-01 right, and your fleet will have eyes.

**The Overlord watches over the fleet.**
**Build it with the care it deserves.**
