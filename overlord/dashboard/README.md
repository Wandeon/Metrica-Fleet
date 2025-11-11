# Metrica Fleet Dashboard

A modern, responsive React/TypeScript dashboard for managing and monitoring your Raspberry Pi fleet.

## 🎯 Features

### Device Management
- **Device Registration**: Register new devices to the fleet
- **Device List**: View all devices with filtering and search
- **Device Details**: Detailed view with real-time metrics
- **Health Monitoring**: Track CPU, memory, disk usage, and temperature
- **Status Tracking**: Monitor device health status in real-time

### Deployment Management
- **Deployment Creation**: Create new deployments with various strategies
- **Deployment Strategies**:
  - **Canary**: Test on small group first
  - **Rolling**: Gradual rollout
  - **Immediate**: All devices at once
  - **Blue-Green**: Zero downtime deployment
- **Progress Tracking**: Monitor deployment progress per device
- **Rollback Support**: Quick rollback on failures

### Alert Management
- **Real-time Alerts**: View and manage system alerts
- **Severity Levels**: Critical, Warning, Info
- **Alert Actions**: Acknowledge, resolve, or silence alerts
- **Device-specific Alerts**: Track alerts by device or fleet-wide

### Fleet Overview
- **Dashboard**: Fleet-wide statistics and health overview
- **Metrics Visualization**: CPU, memory, disk usage averages
- **Recent Activity**: Latest deployments and active alerts
- **Device Statistics**: Breakdown by role, status, and segment

## 🛠 Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Recharts** - Data visualization
- **date-fns** - Date formatting

## 📦 Project Structure

```
dashboard/
├── src/
│   ├── components/          # React components
│   │   ├── common/          # Reusable UI components
│   │   └── Layout.tsx       # Main layout with navigation
│   ├── pages/               # Page components
│   ├── services/            # API service layer
│   ├── hooks/               # Custom React hooks
│   ├── types/               # TypeScript types
│   ├── utils/               # Utility functions
│   ├── App.tsx              # Root component
│   ├── main.tsx             # Application entry point
│   └── index.css            # Global styles
├── vite.config.ts          # Vite configuration
├── tsconfig.json           # TypeScript configuration
├── tailwind.config.js      # Tailwind CSS configuration
├── package.json            # Dependencies
└── Dockerfile              # Docker build configuration
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ (for development)
- npm or yarn
- Fleet API running (see `../api/README.md`)

### Development

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set up environment variables**:
   Create a `.env` file in the dashboard directory:
   ```bash
   VITE_API_URL=http://localhost:8080
   VITE_API_KEY=your-api-key-here
   VITE_GRAFANA_URL=http://localhost:3000
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

   The dashboard will be available at `http://localhost:5173`

4. **Build for production**:
   ```bash
   npm run build
   ```

   Production files will be in the `dist/` directory.

### Docker Deployment

The dashboard is designed to run in Docker as part of the Overlord stack:

```bash
# From the overlord directory
docker compose up -d fleet-dashboard
```

The dashboard will be available at `http://localhost:3001`

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Fleet API base URL | `http://localhost:8080` |
| `VITE_API_KEY` | API authentication key | - |
| `VITE_GRAFANA_URL` | Grafana dashboard URL | `http://localhost:3000` |

### API Integration

The dashboard communicates with the Fleet API at `/api/v1/*` endpoints:

- `/api/v1/devices` - Device management
- `/api/v1/deployments` - Deployment management
- `/api/v1/alerts` - Alert management
- `/api/v1/metrics` - Metrics data

## 📊 Key Pages

### Dashboard (/)
- Fleet-wide statistics
- Device health overview
- Recent deployments and alerts
- Quick access to all sections

### Devices (/devices)
- List all fleet devices
- Filter by status, role, segment
- Search devices
- Register new devices
- View device details

### Deployments (/deployments)
- Create new deployments
- View deployment history
- Monitor deployment progress
- Manage failed deployments

### Alerts (/alerts)
- View active alerts
- Filter by severity and status
- Acknowledge and resolve alerts
- Access runbooks

### Settings (/settings)
- Configure API connection
- Set alert thresholds
- View system information
- Access external monitoring

## 🎨 Customization

### Styling

The dashboard uses Tailwind CSS for styling. Customize colors in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: { /* your colors */ },
      success: { /* your colors */ },
      // ...
    },
  },
}
```

## 🐛 Troubleshooting

### Dashboard won't start

- Check Node.js version (18+)
- Clear `node_modules/` and reinstall
- Check for port conflicts (5173 in dev, 3001 in production)

### Can't connect to API

- Verify `VITE_API_URL` is correct
- Check API is running (`curl http://localhost:8080/health`)
- Verify API key is set correctly
- Check browser console for CORS errors

### Build fails

- Check TypeScript errors: `npm run type-check`
- Verify all dependencies installed
- Clear Vite cache: `rm -rf node_modules/.vite`

## 📝 Development Guidelines

### Code Style

- Use TypeScript for all new files
- Follow React hooks best practices
- Use functional components (no class components)
- Keep components small and focused
- Extract reusable logic into custom hooks

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 🔗 Links

- [Main Repository](https://github.com/Wandeon/Metrica-Fleet)
- [API Documentation](../api/README.md)
- [Deployment Guide](../DEPLOYMENT_GUIDE.md)

---

**Built with ❤️ for efficient Pi fleet management**
