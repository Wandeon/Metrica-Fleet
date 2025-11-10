# Scripts

Deployment, management, and utility scripts for Metrica Fleet.

## Planned Scripts

### Device Agent
- `agent.py` - Main convergence agent (pull, validate, swap)
- `agent.service` - Systemd service definition
- `agent.timer` - Systemd timer for periodic runs

### Atomic Deployment
- `atomic-swap.sh` - Handles atomic directory swapping
- `rollback.sh` - Emergency rollback to previous version
- `validate-deployment.sh` - Post-deployment validation

### Provisioning
- `provision-device.sh` - Initial device setup
- `flash-image.sh` - SD card flashing helper
- `bootstrap.sh` - First-boot configuration

### Monitoring
- `health-check.sh` - Device health verification
- `report-status.sh` - Report to central dashboard
- `collect-logs.sh` - Log aggregation helper

### Maintenance
- `safe-mode.sh` - Enter safe mode
- `force-update.sh` - Manual update trigger
- `cleanup.sh` - Clean old deployments

## Design Guidelines

All scripts should:
- Have timeouts on all operations
- Log to journald/stdout
- Return clear exit codes
- Handle failures gracefully
- Be idempotent where possible
