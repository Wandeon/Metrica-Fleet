# Metrica Fleet

**Zero-touch fleet management system for Raspberry Pi devices with self-healing deployments**

## Overview

Metrica Fleet is a robust, production-ready fleet management system designed to eliminate the chaos of managing distributed Raspberry Pi deployments. Built on hard-learned lessons from real-world fleet operations, it prioritizes reliability, observability, and atomic updates over complexity.

### The Problem

Traditional fleet management breaks down when devices lose connectivity, updates fail halfway, or configurations drift. The "zero-touch fleet" dream turns into 3am SSH debugging sessions when half your devices decide to do their own thing.

### The Solution

Metrica Fleet uses pull-based updates, atomic deployments, and intelligent fallbacks to create a truly resilient fleet where devices self-heal and failures are safe by default.

---

## 🗺️ Documentation Navigation

**👉 START HERE if you're an AI agent or new to the codebase:**

- **[NAVIGATION.md](./NAVIGATION.md)** - Master navigation guide organized by task and component
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - One-page cheat sheet for common operations

**Working on specific components:**

- **Backend API**: [overlord/api/README.md](./overlord/api/README.md) - Adding endpoints, database changes, authentication
- **Monitoring**: [overlord/prometheus/README.md](./overlord/prometheus/README.md) - Metrics, alerts, PromQL queries
- **Dashboards**: [overlord/grafana/README.md](./overlord/grafana/README.md) - Creating dashboards, panels, visualizations
- **Device Roles**: [roles/README.md](./roles/README.md) - Creating and managing device roles
- **Overlord System**: [overlord/README.md](./overlord/README.md) - Deployment, operations, management scripts

**Architecture & Design:**

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Detailed technical design and deployment strategies
- **[IMPLEMENTATION.md](./IMPLEMENTATION.md)** - Implementation roadmap and guidance
- **[SYSTEM_ISOLATION_ASSESSMENT.md](./SYSTEM_ISOLATION_ASSESSMENT.md)** - Security and isolation analysis

---

## Core Principles

### 1. Agent Resilience

A stable agent is non-negotiable. Every agent includes:

- **Timeout for every operation** - No hanging forever
- **Local caching** - Last known good config always available
- **Exponential backoff** - Retry intelligently, not aggressively
- **Watchdog monitoring** - Auto-restart if hung
- **Convergence locking** - No overlapping runs
- **Persistent logging** - Debug without SSH

**Golden Rule**: If anything fails, use last-known-good version instead of going half-configured.

### 2. Pull, Don't Push

Devices pull updates on a role-aware schedule (battery devices stretch to minutes or hours) and can receive event-driven wakeups when the control plane marks an update as ready. No dependency on GitHub Actions, CI/CD pipelines, or merge requirements.

**Update flow**:
1. Read device role and dynamic `update_interval` from local config
2. Hold a lightweight SSE/MQTT subscription for "update available" signals while honoring long sleep windows when idle
3. Hit raw Git URL (or cached artifact service) when signaled or when the interval elapses
4. Compare with current version
5. If new → download → extract → atomic swap → restart → report

If GitHub glitches, devices continue happily with current version.

### 3. Atomic Replace Pattern

Never overwrite running folders. Use symlink swapping:

```
/opt/app_prev      # Previous working version
/opt/app_next      # Incoming update
/opt/app_current   # Symlink to active version
```

**Update sequence**:
1. Download to `/opt/app_next`
2. Validate configuration
3. Swap symlink to `app_next`
4. Restart docker-compose
5. If service fails within N seconds → revert to `app_prev`

This prevents 95% of broken updates requiring manual intervention.

### 4. Agent Outside Docker

Run agents as systemd services, not inside containers:

```bash
systemctl status role-agent
journalctl -u role-agent -n 200
```

Benefits:
- Logs survive container crashes
- Easy debugging without SSH
- Stream logs to Loki/centralized logging
- No silent container failures

### 5. Clean Repository Structure

```
roles/
├── camera-dual/
├── camera-single/
├── audio-player/
├── zigbee-hub/
├── video-player/
└── ai-camera/
common/
scripts/
templates/
```

**Critical rule**: Every role folder must be self-contained. No cross-role dependencies, imports, or symlinks. This eliminates CI edge cases.

### 6. Safe Mode Fallback

When updates fail, devices boot into minimal safe stack:

- Nginx page: "Device in safe mode"
- Tiny API reporting failure details
- Re-deployment request button
- SSH auto-enabled for emergency access

Safe wrong is better than bricked.

### 7. Boring Networking

Avoid MagicDNS unreliability:

- Docker service names for container-to-container
- `127.0.0.1` for host callbacks
- Static hostnames for config pulls

Keep it boring. Boring works.

### 8. Observability First

Every device reports:

- Current role
- Current commit hash
- Last update timestamp
- Last successful convergence
- Health status
- Error summary (if any)

**Monitoring stack**:
- Netdata for metrics
- Loki for log aggregation
- Supabase for device status table
- Dashboard showing fleet health at a glance

No SSH required to know what's happening.

### 9. Short-Lived Agents

Use systemd timers instead of long-running daemons:

```ini
# role-agent.service does one run and exits
# role-agent.timer triggers it every minute
```

Benefits:
- No memory leaks
- No stuck loops
- No locks surviving reboots
- Clean, predictable, stateless

## Architecture Components

### Device Agent

Lightweight service that:
- Sleeps according to its role-defined interval and wakes immediately when the control plane signals an available update
- Downloads and validates new configs
- Performs atomic swaps
- Reports status to central dashboard
- Falls back to safe mode on failure

### Central Dashboard

Web interface showing:
- Fleet overview (all devices at a glance)
- Per-device status and logs
- Manual deployment triggers
- Alert management
- Historical metrics

### Role Definitions

Self-contained Docker Compose stacks for each device role:
- Camera processing
- Audio streaming
- Video playback
- IoT hub
- AI inference
- Custom roles

### Update Pipeline

1. Push code to GitHub
2. Deployment Control promotes the release and emits update signals per rollout segment
3. Devices wake (signal or interval), verify eligibility, and perform atomic updates
4. Automatic rollback if issues detected
5. Dashboard reflects new state

## Getting Started

(Documentation for setup, deployment, and operation coming soon)

## Roadmap

- [ ] Core agent implementation (Python/Go/Bash)
- [ ] Systemd service templates
- [ ] Atomic swap mechanism
- [ ] Safe mode Docker stack
- [ ] Dashboard and API
- [ ] Supabase schema
- [ ] Role templates
- [ ] Device provisioning tools
- [ ] Monitoring integration
- [ ] Complete documentation

## Philosophy

**Metrica Fleet is built on the principle that fleet management should be boring.**

Boring means predictable. Predictable means reliable. Reliable means you sleep through the night instead of SSH debugging at 3am.

---

## License

MIT

## Contributing

Contributions welcome! Please open an issue first to discuss proposed changes.
