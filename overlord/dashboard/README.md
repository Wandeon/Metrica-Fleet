# Metrica Fleet Dashboard

React-based web dashboard for managing the Metrica Fleet.

## Features

- Real-time device status monitoring
- Fleet health overview
- Device management (maintenance mode, version locking)
- Deployment history and control
- Alert viewing
- Device event logs

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Environment Variables

Create a `.env` file:

```
REACT_APP_API_URL=http://localhost:8080
REACT_APP_GRAFANA_URL=http://localhost:3000
```

## Production Deployment

The dashboard is built as a static site and served via Nginx in a Docker container.
