# Device Agent Deployment Guide

This guide explains how to deploy the Metrica Fleet Device Agent to Raspberry Pi devices for centralized fleet management.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Safe Mode](#safe-mode)
- [Uninstallation](#uninstallation)

---

## Overview

The Metrica Fleet Device Agent is a Python service that runs on Raspberry Pi devices and provides:

- **Automatic Registration**: Devices register themselves with the Overlord API on first boot
- **Health Monitoring**: Sends regular heartbeats with system metrics (CPU, memory, disk, temperature)
- **Docker Management**: Monitors running containers and reports failures
- **Configuration Management**: Fetches and applies configuration updates from Overlord
- **Deployment Tracking**: Reports deployment status and maintains update history
- **Safe Mode**: Automatic fallback to minimal operation on critical errors

### Architecture

```
┌─────────────────────┐
│  Raspberry Pi       │
│  ┌──────────────┐   │         ┌─────────────────┐
│  │ Device Agent │───┼────────▶│ Overlord API    │
│  │              │   │  HTTPS  │                 │
│  │ - Metrics    │◀──┼─────────│ - Registration  │
│  │ - Heartbeat  │   │         │ - Configuration │
│  │ - Safe Mode  │   │         │ - Deployments   │
│  └──────────────┘   │         └─────────────────┘
│         │            │
│         ▼            │
│  ┌──────────────┐   │
│  │ Docker Stack │   │
│  │ (Your Apps)  │   │
│  └──────────────┘   │
└─────────────────────┘
```

---

## Prerequisites

### Hardware Requirements

- Raspberry Pi 3B+ or newer
- Minimum 1GB RAM
- 8GB microSD card (16GB+ recommended)
- Network connectivity (Ethernet or WiFi)

### Software Requirements

- Raspberry Pi OS (Bullseye or newer)
- Docker and Docker Compose
- Python 3.9 or newer
- Internet connection for initial setup

### Overlord API

- Running Overlord API server
- API URL (e.g., `http://overlord.example.com:8080`)
- Valid API key for device authentication

---

## Installation

### Option 1: Automated Installation (Recommended)

1. **Copy agent files to device:**

   ```bash
   # From your development machine
   scp -r device-agent/ pi@<device-ip>:~/
   ```

2. **SSH into the device:**

   ```bash
   ssh pi@<device-ip>
   ```

3. **Run installation script:**

   ```bash
   cd ~/device-agent
   sudo ./install-agent.sh
   ```

   The script will:
   - Check prerequisites (Docker, Python3)
   - Create directory structure
   - Install Python dependencies
   - Copy agent files to `/opt/metrica-agent`
   - Create configuration template
   - Install systemd service
   - Enable the service

4. **Edit configuration:**

   ```bash
   sudo nano /etc/metrica-agent/agent.env
   ```

   Set these required values:
   ```bash
   DEVICE_ID=unique-device-name
   DEVICE_ROLE=audio-player
   API_URL=http://overlord.example.com:8080
   API_KEY=your-api-key-here
   ```

5. **Start the service:**

   ```bash
   sudo systemctl start metrica-agent
   ```

### Option 2: Manual Installation

1. **Install dependencies:**

   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-pip docker-ce docker-compose
   ```

2. **Create directories:**

   ```bash
   sudo mkdir -p /opt/metrica-agent
   sudo mkdir -p /etc/metrica-agent
   sudo mkdir -p /var/lib/metrica-agent
   ```

3. **Copy agent files:**

   ```bash
   sudo cp -r ~/device-agent/*.py /opt/metrica-agent/
   sudo cp -r ~/device-agent/safe_mode /opt/metrica-agent/
   sudo cp ~/device-agent/requirements.txt /opt/metrica-agent/
   ```

4. **Install Python packages:**

   ```bash
   sudo pip3 install -r /opt/metrica-agent/requirements.txt
   ```

5. **Create configuration:**

   ```bash
   sudo cp ~/device-agent/.env.example /etc/metrica-agent/agent.env
   sudo nano /etc/metrica-agent/agent.env
   ```

6. **Install systemd service:**

   ```bash
   sudo cp ~/device-agent/metrica-agent.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable metrica-agent
   sudo systemctl start metrica-agent
   ```

---

## Configuration

### Required Settings

Edit `/etc/metrica-agent/agent.env`:

```bash
# Device Identity
DEVICE_ID=device-001                    # Unique identifier (e.g., hostname or serial)
DEVICE_ROLE=audio-player                # Device role (e.g., audio-player, sensor-node)
DEVICE_BRANCH=main                      # Git branch to track (main, develop, etc.)
DEVICE_SEGMENT=stable                   # Deployment segment (stable, beta, canary)

# API Configuration
API_URL=http://overlord.example.com:8080  # Overlord API endpoint
API_KEY=your-api-key-here                 # API authentication key
```

### Optional Settings

```bash
# Agent Behavior
POLL_INTERVAL=60                        # How often to check for updates (seconds)
HEARTBEAT_INTERVAL=30                   # How often to send heartbeats (seconds)
LOG_LEVEL=INFO                          # Logging level (DEBUG, INFO, WARNING, ERROR)

# Repository Configuration
REPO_PATH=/opt/metrica-fleet           # Path to application repository
COMPOSE_FILE=docker-compose.yml        # Docker Compose file name

# Safe Mode Configuration
SAFE_MODE_ENABLED=true                 # Enable automatic safe mode
SAFE_MODE_PORT=8888                    # Port for safe mode status page
DATA_DIR=/var/lib/metrica-agent        # Data directory for agent state
```

### Generating Device ID

Use one of these methods to generate a unique device ID:

```bash
# Option 1: Use hostname
DEVICE_ID=$(hostname)

# Option 2: Use hostname + MAC address
DEVICE_ID=$(hostname)-$(cat /sys/class/net/eth0/address | tr ':' '-')

# Option 3: Use Raspberry Pi serial number
DEVICE_ID=rpi-$(cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2)
```

---

## Verification

### Check Service Status

```bash
sudo systemctl status metrica-agent
```

Expected output:
```
● metrica-agent.service - Metrica Fleet Device Agent
     Loaded: loaded (/etc/systemd/system/metrica-agent.service; enabled)
     Active: active (running) since Mon 2025-11-13 10:00:00 UTC; 5min ago
   Main PID: 1234 (python3)
      Tasks: 3 (limit: 1234)
     Memory: 45.2M
        CPU: 2.345s
     CGroup: /system.slice/metrica-agent.service
             └─1234 /usr/bin/python3 /opt/metrica-agent/agent.py
```

### View Real-Time Logs

```bash
# Follow logs in real-time
sudo journalctl -u metrica-agent -f

# View last 50 lines
sudo journalctl -u metrica-agent -n 50

# View logs from today
sudo journalctl -u metrica-agent --since today
```

### Expected Log Output

Successful startup:
```
Nov 13 10:00:00 device-001 metrica-agent[1234]: [INFO] Starting Metrica Fleet Agent
Nov 13 10:00:00 device-001 metrica-agent[1234]: [INFO] Agent Version: 1.0.0
Nov 13 10:00:00 device-001 metrica-agent[1234]: [INFO] Configuration: role=audio-player, branch=main
Nov 13 10:00:00 device-001 metrica-agent[1234]: [INFO] Initializing agent components...
Nov 13 10:00:00 device-001 metrica-agent[1234]: [INFO] Device registered successfully
Nov 13 10:00:01 device-001 metrica-agent[1234]: [INFO] Entering main loop
Nov 13 10:00:31 device-001 metrica-agent[1234]: [INFO] Heartbeat sent successfully
```

### Check in Overlord Dashboard

1. Open Overlord Dashboard: `http://overlord.example.com:3001`
2. Navigate to "Devices" page
3. Verify your device appears in the list
4. Check that heartbeats are being received (last_seen updates)

### Test API Communication

```bash
# Check if device is registered
curl -H "X-API-Key: your-api-key" \
  http://overlord.example.com:8080/api/devices/device-001

# Check recent heartbeats
curl -H "X-API-Key: your-api-key" \
  http://overlord.example.com:8080/api/v1/devices/device-001/events
```

---

## Troubleshooting

### Agent Won't Start

1. **Check configuration file exists:**
   ```bash
   ls -la /etc/metrica-agent/agent.env
   ```

2. **Validate configuration:**
   ```bash
   sudo cat /etc/metrica-agent/agent.env | grep -E 'DEVICE_ID|API_URL|API_KEY'
   ```

3. **Check Python and dependencies:**
   ```bash
   python3 --version
   pip3 list | grep -E 'requests|docker|psutil'
   ```

4. **View detailed error logs:**
   ```bash
   sudo journalctl -u metrica-agent -n 100 --no-pager
   ```

### Registration Failures

**Symptom:** Agent logs show "Failed to register device"

**Possible causes:**

1. **Network connectivity issue:**
   ```bash
   # Test connection to Overlord
   curl -v http://overlord.example.com:8080/health
   ```

2. **Invalid API key:**
   ```bash
   # Verify API key in config
   grep API_KEY /etc/metrica-agent/agent.env

   # Test API key
   curl -H "X-API-Key: your-key" http://overlord.example.com:8080/api/devices
   ```

3. **Overlord API not running:**
   ```bash
   # Check Overlord status (on Overlord host)
   docker ps | grep fleet-api
   ```

### Heartbeat Failures

**Symptom:** Agent logs show "Failed to send heartbeat"

**Check metrics collection:**
```bash
# Run agent with debug logging
sudo systemctl stop metrica-agent
sudo LOG_LEVEL=DEBUG python3 /opt/metrica-agent/agent.py
```

**Check Docker access:**
```bash
# Verify Docker socket is accessible
ls -la /var/run/docker.sock

# Test Docker access
docker ps
```

### Safe Mode Activated Unexpectedly

**Symptom:** Device enters safe mode, status page visible on port 8888

1. **Check safe mode status:**
   ```bash
   curl http://localhost:8888
   ```

2. **View safe mode lock file:**
   ```bash
   cat /var/lib/metrica-agent/safe-mode.lock | python3 -m json.tool
   ```

3. **View agent logs for error:**
   ```bash
   sudo journalctl -u metrica-agent -n 200 | grep -E 'ERROR|CRITICAL'
   ```

4. **Deactivate safe mode manually:**
   ```bash
   # Stop agent
   sudo systemctl stop metrica-agent

   # Remove safe mode state
   sudo rm /var/lib/metrica-agent/safe-mode.lock

   # Stop safe mode container
   cd /opt/metrica-agent/safe_mode
   sudo docker compose down

   # Start agent
   sudo systemctl start metrica-agent
   ```

### High CPU/Memory Usage

**Check agent resource usage:**
```bash
# View process details
ps aux | grep metrica-agent

# View systemd resource limits
systemctl show metrica-agent | grep -E 'Memory|CPU'
```

**Increase heartbeat interval if needed:**
```bash
sudo nano /etc/metrica-agent/agent.env
# Set: HEARTBEAT_INTERVAL=60
sudo systemctl restart metrica-agent
```

---

## Maintenance

### Updating the Agent

1. **Stop the service:**
   ```bash
   sudo systemctl stop metrica-agent
   ```

2. **Backup configuration:**
   ```bash
   sudo cp /etc/metrica-agent/agent.env /tmp/agent.env.backup
   ```

3. **Copy new agent files:**
   ```bash
   sudo cp -r ~/device-agent-new/*.py /opt/metrica-agent/
   ```

4. **Update dependencies:**
   ```bash
   sudo pip3 install -r /opt/metrica-agent/requirements.txt --upgrade
   ```

5. **Restart the service:**
   ```bash
   sudo systemctl start metrica-agent
   ```

### Rotating Logs

Logs are managed by systemd's journald. Configure log retention:

```bash
sudo nano /etc/systemd/journald.conf
```

Add or modify:
```ini
[Journal]
SystemMaxUse=500M
MaxFileSec=1week
MaxRetentionSec=1month
```

Then restart journald:
```bash
sudo systemctl restart systemd-journald
```

### Monitoring Agent Health

Create a simple health check script:

```bash
#!/bin/bash
# /usr/local/bin/check-agent-health.sh

if systemctl is-active --quiet metrica-agent; then
    echo "✓ Agent is running"

    # Check last heartbeat
    LAST_LOG=$(journalctl -u metrica-agent -n 1 --no-pager | grep "Heartbeat sent")

    if [ -n "$LAST_LOG" ]; then
        echo "✓ Recent heartbeat detected"
        exit 0
    else
        echo "✗ No recent heartbeat"
        exit 1
    fi
else
    echo "✗ Agent is not running"
    exit 1
fi
```

Run via cron every 5 minutes:
```bash
*/5 * * * * /usr/local/bin/check-agent-health.sh || systemctl restart metrica-agent
```

---

## Safe Mode

### What is Safe Mode?

Safe mode is a minimal operational state that activates automatically when:
- Device registration fails after 3 attempts
- Heartbeat failures exceed 5 consecutive attempts
- Any critical error occurs in the main agent loop

### Safe Mode Features

- **Status Page**: Accessible at `http://<device-ip>:8888`
- **Error Display**: Shows reason for safe mode activation
- **System Info**: Displays device ID, hostname, and activation time
- **Recovery Instructions**: Step-by-step guide for manual recovery

### Accessing Safe Mode Status Page

```bash
# From the device
curl http://localhost:8888

# From another machine
curl http://<device-ip>:8888
```

### Manual Safe Mode Activation

```bash
# For testing or manual intervention
cd /opt/metrica-agent/safe_mode
sudo docker compose up -d
```

### Recovering from Safe Mode

**Option 1: Fix issue and restart agent**
```bash
# Fix the underlying issue (network, API key, etc.)
sudo nano /etc/metrica-agent/agent.env

# Restart agent (will auto-deactivate safe mode on success)
sudo systemctl restart metrica-agent
```

**Option 2: Manual deactivation**
```bash
# Remove safe mode state
sudo rm /var/lib/metrica-agent/safe-mode.lock

# Stop safe mode container
cd /opt/metrica-agent/safe_mode
sudo docker compose down

# Restart agent
sudo systemctl restart metrica-agent
```

---

## Uninstallation

### Option 1: Automated Uninstallation

```bash
cd ~/device-agent
sudo ./uninstall-agent.sh
```

The script will:
- Stop and disable the service
- Remove service file
- Remove installation directory
- Optionally remove configuration and data

### Option 2: Manual Uninstallation

```bash
# Stop and disable service
sudo systemctl stop metrica-agent
sudo systemctl disable metrica-agent

# Remove service file
sudo rm /etc/systemd/system/metrica-agent.service
sudo systemctl daemon-reload

# Remove agent files
sudo rm -rf /opt/metrica-agent

# Remove configuration (optional)
sudo rm -rf /etc/metrica-agent

# Remove data (optional)
sudo rm -rf /var/lib/metrica-agent
```

---

## Advanced Configuration

### Running Agent as Non-Root User

Create dedicated user:
```bash
sudo useradd -r -s /bin/false metrica-agent
sudo usermod -aG docker metrica-agent
```

Update service file ownership in `/etc/systemd/system/metrica-agent.service`:
```ini
[Service]
User=metrica-agent
Group=metrica-agent
```

### Firewall Configuration

If using UFW:
```bash
# Allow outbound to Overlord API
sudo ufw allow out to <overlord-ip> port 8080 proto tcp

# Allow inbound for safe mode status page (optional)
sudo ufw allow 8888/tcp
```

### Tailscale Integration

If using Tailscale for secure networking:

1. **Install Tailscale on device:**
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up --authkey=<auth-key>
   ```

2. **Update agent configuration:**
   ```bash
   sudo nano /etc/metrica-agent/agent.env
   ```

   Set:
   ```bash
   API_URL=http://<overlord-tailscale-ip>:8080
   ```

---

## Support

For issues or questions:

- **Documentation**: https://github.com/Wandeon/Metrica-Fleet
- **GitHub Issues**: https://github.com/Wandeon/Metrica-Fleet/issues
- **Logs**: Always include output from `sudo journalctl -u metrica-agent -n 100`

---

**Last Updated**: 2025-11-13
**Agent Version**: 1.0.0
