# Metrica Fleet Overlord

The central management system for the Metrica Pi fleet. This Overlord runs on VPS-01 and provides monitoring, orchestration, and deployment control for all Raspberry Pi devices.

## 🏗️ Architecture

The Overlord consists of these services:

- **PostgreSQL** - Fleet management database
- **Fleet API** - REST API for device registration, status, and deployments
- **Fleet Dashboard** - Web UI for fleet management
- **Prometheus** - Metrics aggregation and alerting
- **Grafana** - Visualization and dashboards
- **Loki** - Centralized log aggregation
- **Alertmanager** - Alert routing and management
- **Nginx** - Reverse proxy and load balancer

## 📋 Prerequisites

- Docker 24.0+ and Docker Compose
- Minimum 4GB RAM
- 20GB available disk space
- Linux (Ubuntu 22.04 LTS recommended)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Wandeon/Metrica-Fleet.git
cd Metrica-Fleet/overlord
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration (IMPORTANT!)
nano .env
```

**Required Configuration Changes:**

```bash
# Database
POSTGRES_PASSWORD=<generate-secure-password>

# Grafana
GRAFANA_ADMIN_PASSWORD=<generate-secure-password>

# API
API_SECRET_KEY=<generate-random-secret-key>

# Optional: Email alerts
SMTP_HOST=smtp.gmail.com:587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Deploy Overlord

```bash
# Run deployment script
./scripts/deploy.sh
```

This will:
- Pull all required Docker images
- Build custom images (API, Dashboard)
- Start all services
- Initialize the database
- Perform health checks

### 4. Access Services

Once deployed, access your services:

- **Fleet Dashboard**: http://localhost:3001
- **Fleet API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **Grafana**: http://localhost:3000 (admin/your-password)
- **Prometheus**: http://localhost:9090

## 📖 Management Scripts

### Deploy/Update

```bash
# Initial deployment
./scripts/deploy.sh

# Update to latest version
./scripts/update.sh
```

### View Logs

```bash
# All services
./scripts/logs.sh

# Specific service
./scripts/logs.sh fleet-api
./scripts/logs.sh postgres
./scripts/logs.sh grafana
```

### Backup

```bash
# Backup all data
./scripts/backup.sh

# Backups are stored in ./backups/ by default
```

### Stop Services

```bash
./scripts/stop.sh
```

## 🔌 API Usage

### Register a Device

```bash
curl -X POST http://localhost:8080/api/v1/devices/register \
  -H "X-API-Key: your-api-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "pi-test-001",
    "hostname": "test-pi",
    "role": "camera-single",
    "branch": "main",
    "segment": "canary",
    "ip_address": "192.168.1.101"
  }'
```

### Send Heartbeat

```bash
curl -X POST http://localhost:8080/api/v1/devices/pi-test-001/heartbeat \
  -H "X-API-Key: your-api-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "healthy",
    "commit_hash": "abc123",
    "uptime_seconds": 86400,
    "cpu_percent": 25.5,
    "memory_percent": 60.2,
    "disk_percent": 45.8,
    "temperature": 55.0
  }'
```

### List Devices

```bash
curl -X GET http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-api-secret-key"
```

## 📊 Monitoring

### Prometheus Metrics

All fleet metrics are available at: http://localhost:9090

Key metrics:
- `fleet_device_status` - Device health status
- `fleet_device_cpu_usage_percent` - CPU usage per device
- `fleet_device_temperature_celsius` - Device temperature
- `fleet_deployment_failures_total` - Deployment failures

### Grafana Dashboards

Pre-configured dashboards:
- **Fleet Overview** - High-level fleet status
- **Device Details** - Per-device metrics
- **Deployment History** - Rollout tracking
- **System Health** - Overlord infrastructure

### Alerts

Configured alerts:
- Device offline (>5 minutes)
- High CPU/Memory/Disk usage
- High temperature (>80°C)
- Deployment failures
- Overlord system issues

## 🔒 Security

### Production Hardening

1. **Change Default Passwords**
   ```bash
   # Update .env file with secure passwords
   nano .env
   ```

2. **Enable HTTPS**
   ```bash
   # Get SSL certificates (Let's Encrypt)
   sudo certbot certonly --standalone -d your-domain.com

   # Copy to nginx/ssl/
   sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem overlord/nginx/ssl/
   sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem overlord/nginx/ssl/

   # Uncomment HTTPS server block in nginx/nginx.conf
   ```

3. **Restrict Access**
   - Configure firewall (UFW, iptables)
   - Use Tailscale for secure device access
   - Restrict Prometheus/Grafana to internal network

4. **Enable Audit Logging**
   ```bash
   # Set in .env
   LOG_LEVEL=info
   ```

### API Authentication

All API endpoints require the `X-API-Key` header. Generate unique keys for each device:

```python
import secrets
device_key = f"fleet_{device_id}_{secrets.token_urlsafe(32)}"
```

## 🧪 Testing

### Health Check

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "database": "connected",
  "device_count": 5
}
```

## 🐛 Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL logs
docker logs fleet-postgres

# Verify credentials
docker exec -it fleet-postgres psql -U fleet -d fleet
```

### API Not Responding

```bash
# Check API logs
./scripts/logs.sh fleet-api

# Restart API service
docker-compose restart fleet-api
```

### High Memory Usage

```bash
# Check container resource usage
docker stats

# Adjust resource limits in docker-compose.yml
```

## 📁 Directory Structure

```
overlord/
├── docker-compose.yml          # Main orchestration file
├── .env.example                # Environment template
├── README.md                   # This file
├── api/                        # Fleet Management API
│   ├── Dockerfile
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── requirements.txt
├── dashboard/                  # Web UI
│   ├── Dockerfile
│   ├── package.json
│   └── nginx.conf
├── prometheus/                 # Metrics & alerting
│   ├── prometheus.yml
│   ├── alerts.yml
│   └── targets/
├── grafana/                    # Dashboards
│   ├── provisioning/
│   └── dashboards/
├── loki/                       # Log aggregation
│   └── loki.yml
├── alertmanager/               # Alert routing
│   └── alertmanager.yml
├── nginx/                      # Reverse proxy
│   └── nginx.conf
├── init-db/                    # Database initialization
│   ├── 01-schema.sql
│   └── 02-seed-data.sql
├── scripts/                    # Management scripts
│   ├── deploy.sh
│   ├── update.sh
│   ├── backup.sh
│   ├── stop.sh
│   └── logs.sh
└── systemd/                    # SystemD service
    └── fleet-overlord.service
```

## 🔄 Backup and Recovery

### Automated Backups

Set up daily backups with cron:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/metrica-fleet/overlord/scripts/backup.sh
```

### Manual Backup

```bash
./scripts/backup.sh
```

### Restore from Backup

```bash
# Stop services
./scripts/stop.sh

# Restore database
gunzip -c backups/postgres_YYYYMMDD_HHMMSS.sql.gz | \
  docker exec -i fleet-postgres psql -U fleet fleet

# Restore configuration
tar -xzf backups/config_YYYYMMDD_HHMMSS.tar.gz

# Start services
./scripts/deploy.sh
```

## 📞 Support

- **Documentation**: https://github.com/Wandeon/Metrica-Fleet
- **Issues**: https://github.com/Wandeon/Metrica-Fleet/issues

## 📜 License

See LICENSE file in the root directory.
