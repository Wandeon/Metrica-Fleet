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
