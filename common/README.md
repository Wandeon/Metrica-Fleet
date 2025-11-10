# Common

Shared resources and configurations used across all roles.

## Contents

### Configuration
- `device-config.json` - Device identity and role assignment
- `agent-config.yml` - Agent behavior settings
- `network.conf` - Network configuration templates

### Docker
- `base-compose.yml` - Common Docker Compose fragments
- `monitoring.yml` - Standard monitoring stack
- `safe-mode.yml` - Safe mode fallback stack

### Libraries
- `lib/` - Shared utility libraries (Python/Bash)
- `validation.sh` - Common validation functions
- `logging.sh` - Logging helpers

### Monitoring
- `netdata.conf` - Netdata configuration
- `loki-config.yml` - Loki agent setup
- `prometheus.yml` - Prometheus scraping config

## Safe Mode Stack

The safe mode stack (`safe-mode.yml`) provides:
- Minimal Nginx with status page
- Health API endpoint
- SSH access
- Basic diagnostics
- Redeployment trigger

This ensures devices are always accessible even when primary role fails.

## Usage

Common resources are pulled by the agent and can be referenced in role-specific configurations.
