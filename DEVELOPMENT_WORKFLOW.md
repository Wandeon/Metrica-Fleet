# Metrica Fleet - Development Workflow Guide

**Managing Production and Development Environments on the Same Device**

---

## Overview

This guide explains how to safely run both **production** and **development** Overlord instances on the same device without conflicts using **git worktrees**.

## Directory Structure

```
/home/admin/
├── Metrica-Fleet/          # Development environment
│   ├── .git/               # Main git repository
│   └── overlord/
│       ├── .env            # Dev credentials & ports
│       └── docker-compose.yml
│
└── Metrica-Fleet-prod/     # Production environment
    └── overlord/
        ├── .env            # Production credentials & ports
        └── docker-compose.yml
```

## Current Setup

```bash
# View all worktrees
$ git worktree list

/home/admin/Metrica-Fleet       [feat/overlord-deployment-assessment]  # Development
/home/admin/Metrica-Fleet-prod  [production]                            # Production
```

### What's Happening

- **Metrica-Fleet/** - Your development directory (current feature branch)
- **Metrica-Fleet-prod/** - Production directory (production branch based on master)
- Both share the same `.git` repository (saves disk space)
- Changes in one don't affect the other until you merge branches

---

## How Git Worktrees Work

### Key Concepts

1. **One Repository, Multiple Checkouts**
   - Single `.git` directory at `/home/admin/Metrica-Fleet/.git`
   - Multiple working directories, each on different branches
   - All share the same commit history

2. **Independent Working Directories**
   - Each worktree has its own files
   - Each can be on a different branch
   - Changes don't affect other worktrees until merged

3. **Branch Protection**
   - Can't check out the same branch in multiple worktrees
   - Forces you to work on different branches (good for safety)

### Visual Example

```
Git Repository (.git/)
    ├─── [feat/overlord-deployment-assessment] → Metrica-Fleet/
    └─── [production] → Metrica-Fleet-prod/
```

---

## Development Workflow

### 1. Working on New Features

```bash
# Navigate to development directory
cd /home/admin/Metrica-Fleet

# Create a new feature branch
git checkout -b feat/implement-dashboard

# Make changes, test, commit
# Your changes are isolated from production
```

### 2. Running Development Overlord

```bash
cd /home/admin/Metrica-Fleet/overlord

# Configure development ports in .env
# API_PORT=18080 (instead of 8080)
# GRAFANA_PORT=13000 (instead of 3000)
# DASHBOARD_PORT=13001 (instead of 3001)

# Start development services
docker compose up -d

# Access dev services:
# - API: http://100.64.123.81:18080
# - Grafana: http://100.64.123.81:13000
# - Dashboard: http://100.64.123.81:13001
```

### 3. Testing Changes

Development environment runs on different ports, so:
- ✅ Production keeps running (unaffected)
- ✅ You can test new code safely
- ✅ Compare dev vs. prod side-by-side
- ✅ No risk of breaking production

### 4. Deploying to Production

```bash
# 1. Test thoroughly in development
cd /home/admin/Metrica-Fleet
docker compose logs -f  # Watch for errors

# 2. Create PR and get approval
git push origin feat/implement-dashboard
gh pr create

# 3. Merge PR to master (via GitHub)

# 4. Update production worktree
cd /home/admin/Metrica-Fleet-prod
git pull origin master  # Get latest approved changes

# 5. Deploy to production
cd overlord
docker compose pull     # Get new images
docker compose up -d    # Update running services
```

---

## Port Allocation Strategy

### Production Ports (Metrica-Fleet-prod/)

| Service | Port | URL |
|---------|------|-----|
| HTTP | 80 | http://100.64.123.81 |
| HTTPS | 443 | https://100.64.123.81 |
| Grafana | 3000 | http://100.64.123.81:3000 |
| Dashboard | 3001 | http://100.64.123.81:3001 |
| API | 8080 | http://100.64.123.81:8080 |
| Prometheus | 9090 | http://100.64.123.81:9090 |
| Alertmanager | 9093 | http://100.64.123.81:9093 |
| Loki | 3100 | http://100.64.123.81:3100 |
| PostgreSQL | 5432 | localhost only |

### Development Ports (Metrica-Fleet/)

| Service | Port | URL |
|---------|------|-----|
| HTTP | 8080 | http://100.64.123.81:8080 |
| HTTPS | 8443 | https://100.64.123.81:8443 |
| Grafana | 13000 | http://100.64.123.81:13000 |
| Dashboard | 13001 | http://100.64.123.81:13001 |
| API | 18080 | http://100.64.123.81:18080 |
| Prometheus | 19090 | http://100.64.123.81:19090 |
| Alertmanager | 19093 | http://100.64.123.81:19093 |
| Loki | 13100 | http://100.64.123.81:13100 |
| PostgreSQL | 15432 | localhost only |

**Rule**: Development ports = Production ports + 10000 (for most services)

---

## Configuration Management

### Production `.env` (Metrica-Fleet-prod/overlord/.env)

```bash
# Production Configuration
POSTGRES_DB=fleet
POSTGRES_PASSWORD=<production-password>
GRAFANA_ADMIN_PASSWORD=<production-password>
API_SECRET_KEY=<production-key>

# Production Ports
API_PORT=8080
GRAFANA_PORT=3000
DASHBOARD_PORT=3001

# Production URLs
API_URL=http://100.64.123.81:8080
GRAFANA_ROOT_URL=http://100.64.123.81:3000
```

### Development `.env` (Metrica-Fleet/overlord/.env)

```bash
# Development Configuration
POSTGRES_DB=fleet_dev
POSTGRES_PASSWORD=<dev-password>
GRAFANA_ADMIN_PASSWORD=<dev-password>
API_SECRET_KEY=<dev-key>

# Development Ports (offset by 10000)
API_PORT=18080
GRAFANA_PORT=13000
DASHBOARD_PORT=13001

# Development URLs
API_URL=http://100.64.123.81:18080
GRAFANA_ROOT_URL=http://100.64.123.81:13000

# Development tweaks
LOG_LEVEL=debug  # More verbose logging
```

**Important**: Development should use **different credentials** for security.

---

## Common Operations

### Adding a New Worktree

```bash
# Create worktree for a specific feature
cd /home/admin/Metrica-Fleet
git worktree add ../Metrica-Fleet-feature feat/new-feature

# Or create worktree with new branch
git worktree add -b feat/experiment ../Metrica-Fleet-experiment
```

### Removing a Worktree

```bash
# Stop services first
cd /home/admin/Metrica-Fleet-experiment/overlord
docker compose down

# Remove worktree
cd /home/admin/Metrica-Fleet
git worktree remove ../Metrica-Fleet-experiment

# Or if directory is already deleted
git worktree prune
```

### Listing All Worktrees

```bash
cd /home/admin/Metrica-Fleet
git worktree list
```

### Checking Worktree Status

```bash
# See which branch each worktree is on
git worktree list

# See changes in specific worktree
cd /home/admin/Metrica-Fleet-prod
git status
```

---

## Docker Compose Management

### Viewing All Running Containers

```bash
# See all containers (both prod and dev)
docker ps

# See only production containers
docker ps | grep fleet-prod

# See only development containers
docker ps | grep fleet-dev
```

### Starting/Stopping Environments

```bash
# Start production
cd /home/admin/Metrica-Fleet-prod/overlord
docker compose up -d

# Start development
cd /home/admin/Metrica-Fleet/overlord
docker compose up -d

# Stop production (for maintenance)
cd /home/admin/Metrica-Fleet-prod/overlord
docker compose down

# Stop development (when done testing)
cd /home/admin/Metrica-Fleet/overlord
docker compose down
```

### Resource Monitoring

```bash
# Check resource usage
docker stats

# Check logs from production
cd /home/admin/Metrica-Fleet-prod/overlord
docker compose logs -f fleet-api

# Check logs from development
cd /home/admin/Metrica-Fleet/overlord
docker compose logs -f fleet-api
```

---

## Best Practices

### 1. Branch Naming

- **Production branch**: `production` (always stable)
- **Development branch**: `develop` or feature branches like `feat/dashboard`
- **Feature branches**: `feat/feature-name`
- **Bugfix branches**: `fix/bug-name`
- **Experiment branches**: `exp/experiment-name`

### 2. Commit Strategy

```bash
# Development worktree - commit frequently
cd /home/admin/Metrica-Fleet
git add .
git commit -m "wip: testing new API endpoint"

# Production worktree - only merge tested code
cd /home/admin/Metrica-Fleet-prod
git pull origin master  # Only pull approved changes
```

### 3. Testing Before Production

Always test in development first:

```bash
# 1. Make changes in dev
cd /home/admin/Metrica-Fleet
# ... edit code ...
git commit -m "feat: add new endpoint"

# 2. Test in dev environment
cd overlord
docker compose up -d
curl http://localhost:18080/api/v1/test-endpoint

# 3. If working, create PR
git push origin feat/new-endpoint
gh pr create

# 4. After PR approval, deploy to prod
cd /home/admin/Metrica-Fleet-prod
git pull origin master
cd overlord
docker compose up -d
```

### 4. Database Separation

**Important**: Production and development should use **separate databases**:

- Production: `fleet` database
- Development: `fleet_dev` database

This prevents test data from polluting production.

### 5. Backup Strategy

```bash
# Backup production before major changes
cd /home/admin/Metrica-Fleet-prod/overlord
./scripts/backup.sh

# Backups stored in ./backups/
ls -lh backups/
```

---

## Troubleshooting

### Issue: Port Already in Use

**Symptom**: Docker can't start because port is already in use

**Solution**: Check which environment is using the port

```bash
# Find which service is using port 8080
ss -tlnp | grep 8080

# Check if prod or dev is running
docker ps | grep fleet

# Stop the conflicting environment
cd /home/admin/Metrica-Fleet-prod/overlord
docker compose down
```

### Issue: Wrong Branch in Worktree

**Symptom**: Made changes in wrong worktree

**Solution**: Stash and move changes

```bash
# In wrong worktree
git stash

# Go to correct worktree
cd /home/admin/Metrica-Fleet-dev

# Apply stashed changes
git stash pop
```

### Issue: Can't Switch Branch (Branch Checked Out)

**Symptom**: `error: 'feat/dashboard' is already checked out at '/home/admin/Metrica-Fleet'`

**Solution**: Branch is checked out in another worktree. Either:
1. Work in that worktree
2. Remove that worktree first
3. Use a different branch

```bash
# See where branch is checked out
git worktree list | grep feat/dashboard

# Remove worktree if not needed
git worktree remove /path/to/worktree
```

### Issue: Worktree Out of Sync

**Symptom**: Worktree doesn't reflect recent commits

**Solution**: Pull latest changes

```bash
cd /home/admin/Metrica-Fleet-prod
git pull origin master

# Or reset to latest
git fetch origin
git reset --hard origin/master
```

---

## Advanced: Multiple Development Environments

You can have multiple development worktrees for different features:

```bash
/home/admin/
├── Metrica-Fleet-prod/       # Production (stable)
├── Metrica-Fleet-dev/        # Main development
├── Metrica-Fleet-dashboard/  # Dashboard work
├── Metrica-Fleet-api/        # API changes
└── Metrica-Fleet-experiment/ # Risky experiments
```

Each runs on different ports:

| Environment | Port Offset | API Port | Grafana |
|-------------|-------------|----------|---------|
| Production | +0 | 8080 | 3000 |
| Development | +10000 | 18080 | 13000 |
| Dashboard | +20000 | 28080 | 23000 |
| API | +30000 | 38080 | 33000 |
| Experiment | +40000 | 48080 | 43000 |

---

## Cleanup

### Disk Space Management

Worktrees share the same git repository, so they use minimal extra space. However, Docker volumes can accumulate:

```bash
# See disk usage by environment
du -sh /home/admin/Metrica-Fleet*

# Clean up unused Docker resources
docker system prune -a --volumes

# Clean up specific environment
cd /home/admin/Metrica-Fleet-dev/overlord
docker compose down -v  # -v removes volumes
```

### Removing All Dev Worktrees

```bash
# Stop all dev containers
docker stop $(docker ps -q)

# Remove all worktrees except main
git worktree list | grep -v "Metrica-Fleet " | awk '{print $1}' | xargs -I {} git worktree remove {}

# Or manually
git worktree remove /home/admin/Metrica-Fleet-prod
```

---

## Quick Reference

### Essential Commands

```bash
# List worktrees
git worktree list

# Add new worktree
git worktree add <path> <branch>

# Remove worktree
git worktree remove <path>

# Switch to production
cd /home/admin/Metrica-Fleet-prod

# Switch to development
cd /home/admin/Metrica-Fleet

# Start prod services
cd /home/admin/Metrica-Fleet-prod/overlord && docker compose up -d

# Start dev services
cd /home/admin/Metrica-Fleet/overlord && docker compose up -d

# View all containers
docker ps

# View prod logs
cd /home/admin/Metrica-Fleet-prod/overlord && docker compose logs -f

# View dev logs
cd /home/admin/Metrica-Fleet/overlord && docker compose logs -f
```

---

## Summary

### Why Worktrees?

✅ **Safety**: Production and development completely isolated
✅ **Convenience**: No branch switching, both run simultaneously
✅ **Efficiency**: Share git history, minimal disk overhead
✅ **Clarity**: Clear separation of stable vs. experimental code
✅ **Speed**: Quick testing without affecting production

### When to Use

- **Use worktrees** when you need to run both prod and dev simultaneously
- **Use branches** when you're only working on one thing at a time
- **Use docker profiles** when you want to test different configurations in same codebase

---

**Last Updated**: 2025-11-11
**Repository**: https://github.com/Wandeon/Metrica-Fleet
