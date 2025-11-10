# Templates

Boilerplate files and templates for creating new roles and components.

## Available Templates

### Role Template
- `role-template/` - Complete role structure
- Includes docker-compose.yml skeleton
- Validation script template
- README template

### Systemd Services
- `device-agent.service` - Agent service template
- `device-agent.timer` - Timer configuration
- `safe-mode.service` - Safe mode activation

### Configuration Files
- `.env.template` - Environment variables template
- `device-config.template.json` - Device configuration
- `docker-compose.template.yml` - Compose file boilerplate

### Scripts
- `validate-template.sh` - Validation script skeleton
- `health-check-template.sh` - Health check template

## Using Templates

1. Copy template to appropriate directory
2. Rename files to match your use case
3. Fill in role-specific details
4. Update README with actual documentation
5. Test thoroughly before deployment

## Creating New Templates

When creating templates:
- Include comprehensive comments
- Provide sensible defaults
- Document all variables
- Keep it simple and clear
- Follow Metrica Fleet principles
