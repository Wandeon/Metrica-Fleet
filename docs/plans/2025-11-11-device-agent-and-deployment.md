# Device Agent and Deployment Continuation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement device agent for Raspberry Pi devices to communicate with Overlord, establish safe mode, and enable automated deployment workflow.

**Architecture:** Python-based agent runs on each device as systemd service, polls Overlord API for configuration updates, reports health metrics, and manages local Docker Compose stacks. Safe mode provides guaranteed SSH access and basic monitoring even when main application fails.

**Tech Stack:** Python 3.11, requests, docker-py, systemd, GitPython, Tailscale

---

## Prerequisites Verification

Before starting, verify Overlord is deployed and healthy:

```bash
cd /home/admin/Metrica-Fleet/overlord
docker compose ps
curl http://localhost:8080/health
```

Expected: All services healthy, API responds with `{"status":"healthy"}`

---

## Task 1: Create Device Agent Structure

**Files:**
- Create: `device-agent/requirements.txt`
- Create: `device-agent/agent.py`
- Create: `device-agent/config.py`
- Create: `device-agent/README.md`
- Create: `tests/test_agent.py`

**Step 1: Create project structure**

```bash
cd /home/admin/Metrica-Fleet
mkdir -p device-agent tests
cd device-agent
```

**Step 2: Write requirements.txt**

Create `device-agent/requirements.txt`:
```txt
requests==2.31.0
docker==7.0.0
gitpython==3.1.40
psutil==5.9.6
pyyaml==6.0.1
python-dotenv==1.0.0
```

**Step 3: Write configuration module**

Create `device-agent/config.py`:
```python
"""Configuration for Metrica Fleet Device Agent"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class AgentConfig:
    """Device agent configuration"""

    # Device Identity
    DEVICE_ID: str = os.getenv("DEVICE_ID", "")
    DEVICE_ROLE: str = os.getenv("DEVICE_ROLE", "unknown")
    DEVICE_BRANCH: str = os.getenv("DEVICE_BRANCH", "main")

    # API Configuration
    API_URL: str = os.getenv("API_URL", "http://localhost:8080")
    API_KEY: str = os.getenv("API_KEY", "")

    # Agent Behavior
    POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL", "60"))  # seconds
    HEARTBEAT_INTERVAL: int = int(os.getenv("HEARTBEAT_INTERVAL", "30"))  # seconds

    # Paths
    REPO_PATH: Path = Path(os.getenv("REPO_PATH", "/opt/metrica-fleet"))
    COMPOSE_FILE: Path = Path(os.getenv("COMPOSE_FILE", "docker-compose.yml"))

    # Safe Mode
    SAFE_MODE_ENABLED: bool = os.getenv("SAFE_MODE_ENABLED", "true").lower() == "true"
    SAFE_MODE_PORT: int = int(os.getenv("SAFE_MODE_PORT", "8888"))

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration"""
        errors = []

        if not cls.DEVICE_ID:
            errors.append("DEVICE_ID is required")

        if not cls.API_URL:
            errors.append("API_URL is required")

        if not cls.REPO_PATH.exists():
            errors.append(f"REPO_PATH does not exist: {cls.REPO_PATH}")

        return errors


config = AgentConfig()
```

**Step 4: Write basic agent skeleton**

Create `device-agent/agent.py`:
```python
"""Metrica Fleet Device Agent

Manages device state, deployment updates, and health reporting.
"""

import sys
import time
import logging
import signal
from typing import Optional
from datetime import datetime

from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("metrica-agent")


class DeviceAgent:
    """Main device agent class"""

    def __init__(self):
        self.running = False
        self.device_id = config.DEVICE_ID

    def start(self):
        """Start the agent"""
        logger.info(f"Starting Metrica Fleet Agent for device: {self.device_id}")

        # Validate configuration
        errors = config.validate()
        if errors:
            logger.error("Configuration errors:")
            for error in errors:
                logger.error(f"  - {error}")
            sys.exit(1)

        self.running = True

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info("Agent started successfully")
        self._run()

    def _run(self):
        """Main agent loop"""
        while self.running:
            try:
                # TODO: Implement polling logic
                logger.debug("Agent running...")
                time.sleep(config.POLL_INTERVAL)
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(5)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def stop(self):
        """Stop the agent"""
        logger.info("Stopping agent...")
        self.running = False


def main():
    """Entry point"""
    agent = DeviceAgent()
    try:
        agent.start()
    except KeyboardInterrupt:
        agent.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 5: Write README**

Create `device-agent/README.md`:
```markdown
# Metrica Fleet Device Agent

Python agent that runs on each Raspberry Pi device, managing deployments and reporting health metrics.

## Installation

```bash
# Install dependencies
pip3 install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with device-specific configuration
```

## Configuration

Required environment variables:
- `DEVICE_ID`: Unique device identifier
- `API_URL`: Overlord API URL
- `API_KEY`: Authentication key

## Running

```bash
# Direct execution
python3 agent.py

# As systemd service
sudo systemctl start metrica-agent
```

## Architecture

- Polls Overlord API every 60 seconds for updates
- Sends heartbeat every 30 seconds
- Manages Docker Compose stacks
- Reports system metrics
- Handles safe mode fallback
```

**Step 6: Commit**

```bash
git add device-agent/ tests/
git commit -m "feat: create device agent structure and configuration"
```

---

## Task 2: Implement API Client

**Files:**
- Create: `device-agent/api_client.py`
- Create: `tests/test_api_client.py`

**Step 1: Write failing test**

Create `tests/test_api_client.py`:
```python
"""Tests for API client"""

import pytest
from unittest.mock import Mock, patch
from device_agent.api_client import APIClient


def test_api_client_initialization():
    """Test API client initializes with config"""
    client = APIClient(
        api_url="http://localhost:8080",
        device_id="test-device-001"
    )

    assert client.api_url == "http://localhost:8080"
    assert client.device_id == "test-device-001"


def test_register_device():
    """Test device registration"""
    client = APIClient(
        api_url="http://localhost:8080",
        device_id="test-device-001"
    )

    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "device_id": "test-device-001",
            "status": "registered"
        }

        result = client.register_device(
            hostname="rpi-001",
            role="audio-player",
            branch="main"
        )

        assert result["status"] == "registered"
        mock_post.assert_called_once()
```

**Step 2: Run test to verify it fails**

```bash
cd /home/admin/Metrica-Fleet
python -m pytest tests/test_api_client.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'device_agent.api_client'"

**Step 3: Implement API client**

Create `device-agent/api_client.py`:
```python
"""API client for communicating with Overlord"""

import logging
import requests
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class APIClient:
    """Client for Overlord API communication"""

    def __init__(self, api_url: str, device_id: str, api_key: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
        self.device_id = device_id
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({
                'X-API-Key': api_key
            })

    def register_device(
        self,
        hostname: str,
        role: str,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """Register device with Overlord"""
        url = f"{self.api_url}/api/devices/register"

        payload = {
            "device_id": self.device_id,
            "hostname": hostname,
            "role": role,
            "branch": branch
        }

        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to register device: {e}")
            raise

    def send_heartbeat(
        self,
        status: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send heartbeat to Overlord"""
        url = f"{self.api_url}/api/devices/{self.device_id}/heartbeat"

        payload = {
            "status": status,
            "timestamp": None,  # Server will set
            "metrics": metrics or {}
        }

        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to send heartbeat: {e}")
            raise

    def get_configuration(self) -> Dict[str, Any]:
        """Get device configuration from Overlord"""
        url = f"{self.api_url}/api/devices/{self.device_id}/config"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to get configuration: {e}")
            raise

    def report_deployment(
        self,
        commit_hash: str,
        status: str,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Report deployment status"""
        url = f"{self.api_url}/api/devices/{self.device_id}/deployments"

        payload = {
            "commit_hash": commit_hash,
            "status": status,
            "error": error
        }

        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to report deployment: {e}")
            raise
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_api_client.py -v
```

Expected: PASS (2 tests pass)

**Step 5: Commit**

```bash
git add device-agent/api_client.py tests/test_api_client.py
git commit -m "feat: implement API client for Overlord communication"
```

---

## Task 3: Implement System Metrics Collection

**Files:**
- Create: `device-agent/metrics.py`
- Create: `tests/test_metrics.py`

**Step 1: Write failing test**

Create `tests/test_metrics.py`:
```python
"""Tests for metrics collection"""

import pytest
from device_agent.metrics import SystemMetrics


def test_collect_system_metrics():
    """Test system metrics collection"""
    metrics = SystemMetrics()
    data = metrics.collect()

    assert "cpu_percent" in data
    assert "memory_percent" in data
    assert "disk_percent" in data
    assert "uptime_seconds" in data
    assert data["cpu_percent"] >= 0
    assert data["memory_percent"] >= 0


def test_collect_docker_metrics():
    """Test Docker container metrics"""
    metrics = SystemMetrics()
    data = metrics.collect_docker_metrics()

    assert "containers_running" in data
    assert "containers_total" in data
    assert isinstance(data["containers_running"], int)
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_metrics.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Implement metrics collection**

Create `device-agent/metrics.py`:
```python
"""System and Docker metrics collection"""

import psutil
import logging
from typing import Dict, Any
from datetime import datetime

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

logger = logging.getLogger(__name__)


class SystemMetrics:
    """Collect system and application metrics"""

    def __init__(self):
        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                logger.warning(f"Docker client unavailable: {e}")
                self.docker_client = None
        else:
            self.docker_client = None

    def collect(self) -> Dict[str, Any]:
        """Collect all system metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "uptime_seconds": int(datetime.now().timestamp() - psutil.boot_time()),
            "temperature": self._get_temperature(),
        }

    def collect_docker_metrics(self) -> Dict[str, Any]:
        """Collect Docker container metrics"""
        if not self.docker_client:
            return {
                "containers_running": 0,
                "containers_total": 0,
                "containers": []
            }

        try:
            containers = self.docker_client.containers.list(all=True)
            running = [c for c in containers if c.status == "running"]

            return {
                "containers_running": len(running),
                "containers_total": len(containers),
                "containers": [
                    {
                        "name": c.name,
                        "status": c.status,
                        "image": c.image.tags[0] if c.image.tags else "unknown"
                    }
                    for c in containers
                ]
            }
        except Exception as e:
            logger.error(f"Failed to collect Docker metrics: {e}")
            return {
                "containers_running": 0,
                "containers_total": 0,
                "containers": [],
                "error": str(e)
            }

    def _get_temperature(self) -> float:
        """Get CPU temperature (Raspberry Pi specific)"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0
                return round(temp, 1)
        except Exception:
            return 0.0
```

**Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_metrics.py -v
```

Expected: PASS (2 tests pass)

**Step 5: Commit**

```bash
git add device-agent/metrics.py tests/test_metrics.py
git commit -m "feat: implement system and Docker metrics collection"
```

---

## Task 4: Implement Safe Mode

**Files:**
- Create: `device-agent/safe_mode.py`
- Create: `safe-mode/docker-compose.yml`
- Create: `safe-mode/status-page/index.html`

**Step 1: Create safe mode Docker Compose stack**

Create `safe-mode/docker-compose.yml`:
```yaml
version: '3.8'

services:
  status-page:
    image: nginx:alpine
    container_name: safe-mode-status
    restart: always
    ports:
      - "8888:80"
    volumes:
      - ./status-page:/usr/share/nginx/html:ro
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://127.0.0.1:80"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  default:
    name: safe-mode-network
```

**Step 2: Create status page**

Create `safe-mode/status-page/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Safe Mode - Metrica Fleet</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 3rem;
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }
        h1 { font-size: 3rem; margin: 0; }
        p { font-size: 1.2rem; opacity: 0.9; }
        .status {
            background: rgba(255, 255, 255, 0.2);
            padding: 1rem;
            border-radius: 10px;
            margin-top: 2rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Safe Mode Active</h1>
        <p>This device is running in safe mode</p>
        <div class="status">
            <p><strong>Device:</strong> <span id="device-id">Loading...</span></p>
            <p><strong>Status:</strong> Awaiting instructions</p>
            <p><strong>SSH:</strong> Available on port 22</p>
        </div>
    </div>
    <script>
        // Get device ID from hostname
        document.getElementById('device-id').textContent = window.location.hostname;
    </script>
</body>
</html>
```

**Step 3: Implement safe mode manager**

Create `device-agent/safe_mode.py`:
```python
"""Safe mode management"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class SafeMode:
    """Manage safe mode activation and status"""

    def __init__(self, safe_mode_path: Path):
        self.safe_mode_path = safe_mode_path
        self.compose_file = safe_mode_path / "docker-compose.yml"

    def activate(self) -> bool:
        """Activate safe mode"""
        logger.warning("Activating safe mode...")

        try:
            # Stop main application
            logger.info("Stopping main application...")
            subprocess.run(
                ["docker", "compose", "down"],
                cwd="/opt/metrica-fleet",
                capture_output=True,
                timeout=60
            )

            # Start safe mode
            logger.info("Starting safe mode services...")
            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=self.safe_mode_path,
                capture_output=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info("Safe mode activated successfully")
                return True
            else:
                logger.error(f"Failed to activate safe mode: {result.stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error activating safe mode: {e}")
            return False

    def deactivate(self) -> bool:
        """Deactivate safe mode"""
        logger.info("Deactivating safe mode...")

        try:
            result = subprocess.run(
                ["docker", "compose", "down"],
                cwd=self.safe_mode_path,
                capture_output=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info("Safe mode deactivated")
                return True
            else:
                logger.error(f"Failed to deactivate safe mode: {result.stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"Error deactivating safe mode: {e}")
            return False

    def is_active(self) -> bool:
        """Check if safe mode is active"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=safe-mode", "--format", "{{.Names}}"],
                capture_output=True,
                text=True
            )
            return "safe-mode" in result.stdout
        except Exception:
            return False
```

**Step 4: Test safe mode manually**

```bash
cd /home/admin/Metrica-Fleet/safe-mode
docker compose up -d
curl http://localhost:8888
docker compose down
```

Expected: Status page displays, safe mode container runs

**Step 5: Commit**

```bash
git add safe-mode/ device-agent/safe_mode.py
git commit -m "feat: implement safe mode with status page"
```

---

## Task 5: Integrate Agent Components

**Files:**
- Modify: `device-agent/agent.py`
- Create: `device-agent/.env.example`

**Step 1: Update main agent to use new components**

Modify `device-agent/agent.py` (replace _run method):
```python
def _run(self):
    """Main agent loop"""
    last_heartbeat = 0
    last_config_check = 0

    # Initialize components
    from api_client import APIClient
    from metrics import SystemMetrics

    api_client = APIClient(
        api_url=config.API_URL,
        device_id=config.DEVICE_ID,
        api_key=config.API_KEY
    )
    metrics = SystemMetrics()

    # Register device on startup
    try:
        import socket
        hostname = socket.gethostname()
        result = api_client.register_device(
            hostname=hostname,
            role=config.DEVICE_ROLE,
            branch=config.DEVICE_BRANCH
        )
        logger.info(f"Device registered: {result}")
    except Exception as e:
        logger.error(f"Failed to register device: {e}")

    while self.running:
        try:
            current_time = time.time()

            # Send heartbeat
            if current_time - last_heartbeat >= config.HEARTBEAT_INTERVAL:
                system_metrics = metrics.collect()
                docker_metrics = metrics.collect_docker_metrics()

                all_metrics = {**system_metrics, **docker_metrics}

                try:
                    api_client.send_heartbeat(
                        status="running",
                        metrics=all_metrics
                    )
                    logger.debug("Heartbeat sent")
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}")

                last_heartbeat = current_time

            # Check for configuration updates
            if current_time - last_config_check >= config.POLL_INTERVAL:
                try:
                    cfg = api_client.get_configuration()
                    logger.debug(f"Configuration: {cfg}")
                    # TODO: Process configuration updates
                except Exception as e:
                    logger.error(f"Failed to get configuration: {e}")

                last_config_check = current_time

            time.sleep(1)  # Short sleep, use timestamps for intervals

        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(5)
```

**Step 2: Create environment example**

Create `device-agent/.env.example`:
```bash
# Device Identity
DEVICE_ID=device-001
DEVICE_ROLE=audio-player
DEVICE_BRANCH=main

# API Configuration
API_URL=http://overlord.local:8080
API_KEY=your-api-key-here

# Agent Behavior
POLL_INTERVAL=60
HEARTBEAT_INTERVAL=30

# Paths
REPO_PATH=/opt/metrica-fleet
COMPOSE_FILE=docker-compose.yml

# Safe Mode
SAFE_MODE_ENABLED=true
SAFE_MODE_PORT=8888
```

**Step 3: Test agent startup**

```bash
cd /home/admin/Metrica-Fleet/device-agent
cp .env.example .env
# Edit .env with test values
python3 agent.py
```

Expected: Agent starts, attempts registration, sends heartbeats (will fail without Overlord API accepting requests)

**Step 4: Commit**

```bash
git add device-agent/agent.py device-agent/.env.example
git commit -m "feat: integrate agent components for full operation"
```

---

## Task 6: Create Systemd Service

**Files:**
- Create: `device-agent/metrica-agent.service`
- Create: `scripts/install-agent.sh`

**Step 1: Create systemd service file**

Create `device-agent/metrica-agent.service`:
```ini
[Unit]
Description=Metrica Fleet Device Agent
After=network-online.target docker.service
Wants=network-online.target
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/metrica-fleet/device-agent
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=/opt/metrica-fleet/device-agent/.env
ExecStart=/usr/bin/python3 /opt/metrica-fleet/device-agent/agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Step 2: Create installation script**

Create `scripts/install-agent.sh`:
```bash
#!/bin/bash
set -e

echo "Installing Metrica Fleet Device Agent..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# Install dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip git docker.io docker-compose

# Create installation directory
INSTALL_DIR="/opt/metrica-fleet"
echo "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Clone or copy repository
if [ -d "/home/admin/Metrica-Fleet" ]; then
    echo "Copying from local repository..."
    cp -r /home/admin/Metrica-Fleet/* "$INSTALL_DIR/"
else
    echo "Cloning from remote repository..."
    git clone https://github.com/YOUR_ORG/Metrica-Fleet.git "$INSTALL_DIR"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
cd "$INSTALL_DIR/device-agent"
pip3 install -r requirements.txt

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit /opt/metrica-fleet/device-agent/.env with your device configuration"
    echo ""
fi

# Install systemd service
echo "Installing systemd service..."
cp metrica-agent.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable metrica-agent

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit /opt/metrica-fleet/device-agent/.env"
echo "2. Set DEVICE_ID, API_URL, and API_KEY"
echo "3. Start the agent: systemctl start metrica-agent"
echo "4. Check status: systemctl status metrica-agent"
echo "5. View logs: journalctl -u metrica-agent -f"
```

**Step 3: Make script executable**

```bash
chmod +x scripts/install-agent.sh
```

**Step 4: Test installation script (dry run)**

```bash
# Review the script
cat scripts/install-agent.sh
```

**Step 5: Commit**

```bash
git add device-agent/metrica-agent.service scripts/install-agent.sh
git commit -m "feat: add systemd service and installation script"
```

---

## Task 7: Update Overlord API Endpoints

**Context:** The API needs endpoints to handle device registration and heartbeats.

**Files:**
- Modify: `overlord/api/main.py`
- Modify: `overlord/api/models.py`

**Step 1: Verify current API endpoints**

```bash
cd /home/admin/Metrica-Fleet/overlord
curl http://localhost:8080/docs
```

Expected: API docs page, check if `/api/devices/register` endpoint exists

**Step 2: Add device registration endpoint**

Add to `overlord/api/main.py`:
```python
@app.post("/api/devices/register")
async def register_device(
    device_id: str = Body(...),
    hostname: str = Body(...),
    role: str = Body(...),
    branch: str = Body("main"),
    db: AsyncSession = Depends(get_db)
):
    """Register a new device or update existing device"""

    # Check if device exists
    result = await db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    device = result.scalar_one_or_none()

    if device:
        # Update existing device
        device.hostname = hostname
        device.role = role
        device.branch = branch
        device.status = "online"
        device.last_seen = func.now()
    else:
        # Create new device
        device = Device(
            device_id=device_id,
            hostname=hostname,
            role=role,
            branch=branch,
            status="online",
            first_registered=func.now(),
            last_seen=func.now()
        )
        db.add(device)

    await db.commit()
    await db.refresh(device)

    return {
        "device_id": device.device_id,
        "status": "registered",
        "message": "Device registered successfully"
    }
```

**Step 3: Add heartbeat endpoint**

Add to `overlord/api/main.py`:
```python
@app.post("/api/devices/{device_id}/heartbeat")
async def device_heartbeat(
    device_id: str,
    status: str = Body(...),
    metrics: dict = Body({}),
    db: AsyncSession = Depends(get_db)
):
    """Receive device heartbeat"""

    # Get device
    result = await db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Update device status
    device.status = status
    device.last_seen = func.now()

    # Update metrics if provided
    if metrics:
        device.cpu_usage_percent = metrics.get("cpu_percent")
        device.memory_usage_percent = metrics.get("memory_percent")
        device.disk_usage_percent = metrics.get("disk_percent")
        device.uptime_seconds = metrics.get("uptime_seconds")
        device.temperature_celsius = metrics.get("temperature")

    # Create heartbeat record
    heartbeat = DeviceHeartbeat(
        device_id=device_id,
        status=status,
        cpu_percent=metrics.get("cpu_percent"),
        memory_percent=metrics.get("memory_percent"),
        disk_percent=metrics.get("disk_percent"),
        temperature=metrics.get("temperature"),
        containers_running=metrics.get("containers_running"),
        containers_failed=metrics.get("containers_total", 0) - metrics.get("containers_running", 0),
        heartbeat_metadata=metrics
    )
    db.add(heartbeat)

    await db.commit()

    return {
        "device_id": device_id,
        "status": "acknowledged",
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Step 4: Add get configuration endpoint**

Add to `overlord/api/main.py`:
```python
@app.get("/api/devices/{device_id}/config")
async def get_device_config(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get device configuration"""

    result = await db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return {
        "device_id": device.device_id,
        "branch": device.branch,
        "current_commit_hash": device.current_commit_hash,
        "update_enabled": device.update_enabled,
        "version_lock": device.version_lock,
        "maintenance_mode": device.maintenance_mode,
        "config": device.device_metadata
    }
```

**Step 5: Restart API to apply changes**

```bash
cd /home/admin/Metrica-Fleet/overlord
docker compose restart fleet-api
sleep 5
curl http://localhost:8080/docs
```

Expected: New endpoints visible in API docs

**Step 6: Commit**

```bash
git add overlord/api/main.py
git commit -m "feat: add device registration and heartbeat API endpoints"
```

---

## Task 8: Create Deployment Documentation

**Files:**
- Create: `docs/DEVICE_DEPLOYMENT.md`

**Step 1: Write deployment guide**

Create `docs/DEVICE_DEPLOYMENT.md`:
```markdown
# Device Deployment Guide

Step-by-step guide for deploying Metrica Fleet to Raspberry Pi devices.

## Prerequisites

- Raspberry Pi 4 (2GB+ RAM recommended)
- Raspberry Pi OS Lite (64-bit)
- Network connectivity
- Tailscale installed (optional but recommended)

## Initial Device Setup

### 1. Prepare Raspberry Pi

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y git curl python3 python3-pip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Reboot
sudo reboot
```

### 2. Install Tailscale (Recommended)

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### 3. Set Device Identity

```bash
# Generate unique device ID based on hostname and MAC
DEVICE_ID="device-$(hostname)-$(cat /sys/class/net/eth0/address | tr -d ':')"
echo "Device ID: $DEVICE_ID"
```

## Agent Installation

### 1. Download Installation Script

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_ORG/Metrica-Fleet/main/scripts/install-agent.sh -o install-agent.sh
chmod +x install-agent.sh
```

### 2. Run Installation

```bash
sudo ./install-agent.sh
```

### 3. Configure Agent

Edit `/opt/metrica-fleet/device-agent/.env`:

```bash
sudo nano /opt/metrica-fleet/device-agent/.env
```

Set required values:
```bash
DEVICE_ID=your-device-id-here
API_URL=http://overlord.tailscale-ip:8080
API_KEY=your-api-key-here
DEVICE_ROLE=audio-player  # or other role
```

### 4. Start Agent

```bash
sudo systemctl start metrica-agent
sudo systemctl status metrica-agent
```

### 5. Verify Operation

```bash
# Check agent logs
sudo journalctl -u metrica-agent -f

# Verify device appears in Overlord dashboard
curl http://overlord.local:8080/api/devices
```

## Troubleshooting

### Agent Won't Start

```bash
# Check configuration
sudo cat /opt/metrica-fleet/device-agent/.env

# Check logs
sudo journalctl -u metrica-agent -n 50 --no-pager

# Test network connectivity
curl http://overlord.local:8080/health
```

### Device Not Appearing in Dashboard

1. Verify DEVICE_ID is unique
2. Check API_URL is correct
3. Verify API_KEY if authentication is enabled
4. Check firewall rules

## Safe Mode Recovery

If device becomes unresponsive:

```bash
# SSH to device
ssh pi@device-ip

# Activate safe mode
cd /opt/metrica-fleet/safe-mode
docker compose up -d

# Access status page
curl http://device-ip:8888
```

## Next Steps

- Configure device role in Overlord
- Assign to deployment group
- Monitor in Grafana dashboard
```

**Step 2: Commit**

```bash
git add docs/DEVICE_DEPLOYMENT.md
git commit -m "docs: add comprehensive device deployment guide"
```

---

## Verification Checklist

After completing all tasks, verify:

### Agent Functionality
```bash
# Agent can be installed
sudo ./scripts/install-agent.sh

# Agent service starts
sudo systemctl start metrica-agent
sudo systemctl status metrica-agent

# Agent sends heartbeats (check logs)
sudo journalctl -u metrica-agent -n 20
```

### API Endpoints
```bash
# Registration endpoint works
curl -X POST http://localhost:8080/api/devices/register \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test-001","hostname":"test-pi","role":"audio-player"}'

# Heartbeat endpoint works
curl -X POST http://localhost:8080/api/devices/test-001/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"status":"running","metrics":{"cpu_percent":25}}'

# Config endpoint works
curl http://localhost:8080/api/devices/test-001/config
```

### Safe Mode
```bash
# Safe mode can be activated
cd safe-mode
docker compose up -d

# Status page accessible
curl http://localhost:8888

# Safe mode can be stopped
docker compose down
```

### Documentation
- [ ] Installation guide is clear and complete
- [ ] All required configuration variables documented
- [ ] Troubleshooting section covers common issues

---

## Next Steps After This Plan

1. **Test on Real Hardware**
   - Deploy agent to actual Raspberry Pi
   - Verify all functionality
   - Test network resilience

2. **Implement Git-Based Updates**
   - Agent polls for new commits
   - Downloads and applies updates
   - Rollback on failure

3. **Add Alerting**
   - Configure Prometheus alerts
   - Set up Alertmanager notifications
   - Test alert delivery

4. **Production Hardening**
   - Enable API authentication
   - Configure SSL/TLS
   - Set up monitoring alerts
   - Implement backup strategy

5. **Deployment Automation**
   - Create fleet deployment scripts
   - Implement gradual rollout
   - Add canary deployment support
