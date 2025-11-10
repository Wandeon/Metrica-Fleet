# Roles

This directory contains self-contained role definitions for different device types in the Metrica Fleet.

## Design Principles

Each role folder must be:
- **Self-contained**: No cross-role dependencies
- **Complete**: All necessary configs, compose files, and scripts included
- **Validated**: Include validation script for config checking
- **Documented**: README explaining purpose and requirements

## Structure

Each role should follow this structure:

```
role-name/
├── docker-compose.yml    # Main service definition
├── .env.example          # Environment variables template
├── config/               # Role-specific configuration files
├── validate.sh           # Configuration validation script
└── README.md             # Role documentation
```

## Available Roles

- **camera-dual**: Dual camera processing and streaming
- **camera-single**: Single camera setup
- **audio-player**: Audio streaming and playback
- **zigbee-hub**: Zigbee IoT device hub
- **video-player**: Video playback and display
- **ai-camera**: AI-powered camera with inference

## Adding New Roles

1. Create new directory under `roles/`
2. Add docker-compose.yml with all services
3. Include validation script
4. Document requirements and setup
5. Test atomic deployment workflow
6. No dependencies on other roles
