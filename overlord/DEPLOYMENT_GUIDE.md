# VPS-01 Overlord Deployment Guide

Complete step-by-step guide to deploy the Metrica Fleet Overlord on your VPS-01 server.

## 📋 Pre-Deployment Checklist

### VPS Requirements

- [ ] Ubuntu 22.04 LTS (or similar)
- [ ] Minimum 4GB RAM (8GB recommended)
- [ ] 20GB+ available disk space
- [ ] Public IP address or domain name
- [ ] SSH access with sudo privileges

### Software Requirements

- [ ] Docker 24.0+
- [ ] Docker Compose V2
- [ ] Git
- [ ] SSL certificates (optional but recommended)

## 🚀 Step-by-Step Deployment

### Step 1: Prepare VPS-01

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git curl wget ufw

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose V2
sudo apt install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### Step 2: Create Fleet User

```bash
# Create dedicated user for fleet management
sudo useradd -r -m -s /bin/bash fleet
sudo usermod -aG docker fleet

# Switch to fleet user
sudo su - fleet
```

### Step 3: Clone Repository

```bash
# Clone the Metrica Fleet repository
cd /opt
sudo mkdir -p metrica-fleet
sudo chown fleet:fleet metrica-fleet
cd metrica-fleet

git clone https://github.com/Wandeon/Metrica-Fleet.git .
cd overlord
```

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate secure passwords
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)" >> .env.tmp
echo "GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 24)" >> .env.tmp
echo "API_SECRET_KEY=$(openssl rand -base64 48)" >> .env.tmp

# Edit .env file
nano .env
```

**Required .env Configuration:**

```bash
# Database (REQUIRED)
POSTGRES_DB=fleet
POSTGRES_USER=fleet
POSTGRES_PASSWORD=<paste-generated-password>

# Grafana (REQUIRED)
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<paste-generated-password>
GRAFANA_ROOT_URL=http://your-vps-ip:3000
GRAFANA_PORT=3000

# Fleet API (REQUIRED)
API_PORT=8080
API_SECRET_KEY=<paste-generated-key>
API_URL=http://your-vps-ip:8080

# Dashboard
DASHBOARD_PORT=3001

# Email Alerts (OPTIONAL)
SMTP_HOST=smtp.gmail.com:587
SMTP_FROM=alerts@your-domain.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_DEFAULT=admin@your-domain.com

# Logging
LOG_LEVEL=info
```

### Step 5: Configure Firewall

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (IMPORTANT: Do this first!)
sudo ufw allow 22/tcp

# Allow Overlord services
sudo ufw allow 80/tcp        # HTTP
sudo ufw allow 443/tcp       # HTTPS
sudo ufw allow 3000/tcp      # Grafana
sudo ufw allow 3001/tcp      # Dashboard
sudo ufw allow 8080/tcp      # API

# Check status
sudo ufw status
```

### Step 6: Deploy Overlord

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run deployment
./scripts/deploy.sh
```

The deployment script will:
1. ✅ Check dependencies
2. ✅ Load configuration
3. ✅ Create directories
4. ✅ Pull Docker images
5. ✅ Build custom images
6. ✅ Start all services
7. ✅ Initialize database
8. ✅ Perform health checks

### Step 7: Verify Deployment

```bash
# Check all services are running
docker ps

# Expected output: 9 containers running
# - fleet-postgres
# - fleet-prometheus
# - fleet-grafana
# - fleet-loki
# - fleet-alertmanager
# - fleet-api
# - fleet-dashboard
# - fleet-nginx

# Check service health
curl http://localhost:8080/health

# View logs
./scripts/logs.sh
```

### Step 8: Access Services

Open your browser and navigate to:

- **Fleet Dashboard**: http://your-vps-ip:3001
- **Fleet API Docs**: http://your-vps-ip:8080/docs
- **Grafana**: http://your-vps-ip:3000
  - Username: `admin`
  - Password: (from your .env file)

### Step 9: Enable SystemD Service (Optional)

For auto-start on boot:

```bash
# Copy systemd service file
sudo cp systemd/fleet-overlord.service /etc/systemd/system/

# Update paths in service file
sudo nano /etc/systemd/system/fleet-overlord.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable fleet-overlord.service
sudo systemctl start fleet-overlord.service

# Check status
sudo systemctl status fleet-overlord.service
```

### Step 10: Set Up Backups

```bash
# Create backup directory
mkdir -p /opt/metrica-fleet/backups

# Test backup
./scripts/backup.sh

# Set up automated daily backups (2 AM)
crontab -e

# Add this line:
0 2 * * * /opt/metrica-fleet/overlord/scripts/backup.sh >> /var/log/fleet-backup.log 2>&1
```

## 🔒 Production Hardening

### Enable HTTPS with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot

# Stop nginx temporarily
docker compose stop nginx

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/
sudo chown fleet:fleet nginx/ssl/*

# Edit nginx configuration
nano nginx/nginx.conf
# Uncomment HTTPS server block and update server_name

# Restart nginx
docker compose restart nginx

# Set up auto-renewal
sudo crontab -e
# Add: 0 3 * * * certbot renew --quiet --deploy-hook "docker compose -f /opt/metrica-fleet/overlord/docker-compose.yml restart nginx"
```

### Restrict Access

```bash
# Edit nginx config to restrict Prometheus/metrics
nano nginx/nginx.conf

# Uncomment access restrictions:
# location /metrics {
#     allow 10.0.0.0/8;    # Internal network
#     deny all;
# }
#
# location /prometheus/ {
#     allow 10.0.0.0/8;
#     deny all;
# }
```

### Enable Fail2Ban

```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Create jail for API
sudo nano /etc/fail2ban/jail.d/fleet-api.conf

# Add:
[fleet-api]
enabled = true
port = 8080
filter = fleet-api
logpath = /opt/metrica-fleet/overlord/logs/api.log
maxretry = 5
bantime = 3600
```

## 📊 Post-Deployment Tasks

### 1. Configure Grafana

1. Login to Grafana (http://your-vps-ip:3000)
2. Change admin password
3. Verify datasources are connected
4. Import additional dashboards if needed

### 2. Test Alert Manager

```bash
# Send test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {"alertname": "TestAlert", "severity": "info"},
    "annotations": {"summary": "Test alert from Overlord"}
  }]'

# Check email was received
```

### 3. Register First Device

```bash
# Get API key from .env
API_KEY=$(grep API_SECRET_KEY .env | cut -d'=' -f2)

# Register test device
curl -X POST http://localhost:8080/api/v1/devices/register \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "pi-test-001",
    "hostname": "test-pi",
    "role": "camera-single",
    "branch": "staging",
    "segment": "canary",
    "ip_address": "192.168.1.101"
  }'

# Verify device appears in dashboard
```

## 🧪 Testing Checklist

- [ ] All Docker containers are running
- [ ] Database is accessible (psql test)
- [ ] API health check returns 200 OK
- [ ] Grafana dashboard loads
- [ ] Prometheus targets are up
- [ ] Loki is receiving logs
- [ ] Alert manager is configured
- [ ] Test device registration works
- [ ] Metrics are being collected
- [ ] Backups are working

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
./scripts/logs.sh <service-name>

# Check disk space
df -h

# Check memory
free -h

# Restart specific service
docker compose restart <service-name>
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
docker exec -it fleet-postgres psql -U fleet -d fleet -c "\dt"

# Reset database (WARNING: destroys data)
docker compose down -v
docker compose up -d
```

### API Authentication Errors

```bash
# Verify API key in .env
grep API_SECRET_KEY .env

# Test with correct key
curl -H "X-API-Key: your-actual-key" http://localhost:8080/health
```

### High Resource Usage

```bash
# Check container stats
docker stats

# Reduce Prometheus retention (in prometheus.yml)
--storage.tsdb.retention.time=30d

# Reduce log retention (in loki.yml)
retention_period: 360h  # 15 days
```

## 📈 Monitoring the Overlord

### Key Metrics to Watch

- Overlord CPU usage (should be <50% idle)
- Overlord memory usage (should be <85%)
- Disk usage (alert at 80%)
- Database connections
- API request rate and latency
- Container health status

### Grafana Dashboards

Create alerts for:
- Overlord high CPU/memory
- Database connection failures
- API error rate >5%
- Disk space <20%

## 🔄 Updates and Maintenance

### Update Overlord

```bash
# Pull latest changes
git pull origin main

# Run update script
./scripts/update.sh

# Verify all services are healthy
docker ps
./scripts/logs.sh
```

### Database Migrations

```bash
# Backup before migration
./scripts/backup.sh

# Apply migrations (future)
# docker exec -it fleet-api alembic upgrade head
```

## 📞 Need Help?

- **Documentation**: Check the main README.md
- **Logs**: `./scripts/logs.sh [service]`
- **Status**: `docker ps` and `docker stats`
- **Health**: `curl http://localhost:8080/health`

## ✅ Deployment Complete!

Your Overlord is now ready to manage your Pi fleet. Next steps:

1. Configure your first role (camera-single, etc.)
2. Deploy the agent to your first Pi device
3. Watch metrics flow into Grafana
4. Set up deployment pipelines
5. Scale to your full fleet

---

**Congratulations! Your VPS-01 Overlord is operational.** 🎉
