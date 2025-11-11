# Claude Code Instructions - Metrica Fleet Development

**Repository**: Metrica Fleet - Zero-touch fleet management for Raspberry Pi devices
**Current Date**: 2025-11-11
**Last Updated**: 2025-11-11

---

## Development Workflow

This repository uses a **simple branch-based workflow**:

### Directory Structure

```
/home/admin/
└── Metrica-Fleet/          # Single repository
    ├── Branch: develop (active development)
    │   └── Purpose: Feature implementation, testing, day-to-day work
    │
    └── Branch: master (production)
        └── Purpose: Stable, tested code ready for deployment
```

### How It Works

- **One directory**: `/home/admin/Metrica-Fleet`
- **One set of ports**: 8080 (API), 3000 (Grafana), 3001 (Dashboard)
- **Switch branches** as needed: `git checkout develop` or `git checkout master`
- **Stop services** when switching between development and production deployments

---

## Branch Strategy

### Main Branches

1. **master** (protected, production)
   - Stable, approved code for production deployment
   - Only updated via merged PRs from develop
   - Source of truth for releases
   - Deploy from this branch

2. **develop** (active development)
   - Integration branch for ongoing work
   - All feature branches merge here first
   - Your default working branch

### Feature Branches

- **Naming**: `feat/feature-name`, `fix/bug-name`, `docs/description`
- **Base**: Always branch from `develop`
- **Location**: Work in `/home/admin/Metrica-Fleet/`

---

## Standard Development Process

### 1. Starting New Work

```bash
# Navigate to repository
cd /home/admin/Metrica-Fleet

# Ensure develop is up to date
git checkout develop
git pull origin develop

# Create feature branch (optional, can work directly on develop)
git checkout -b feat/your-feature-name

# Make changes, commit regularly
git add .
git commit -m "feat: description of change"
```

### 2. Testing Changes

```bash
# In development worktree (/home/admin/Metrica-Fleet)
cd overlord

# Use development ports (18080, 13000, 13001)
# Check/edit .env for dev configuration
docker compose up -d

# Test thoroughly
# Check logs: docker compose logs -f
```

### 3. Creating Pull Request

```bash
# Push feature branch
git push origin feat/your-feature-name

# Create PR to develop branch (NOT master)
gh pr create --base develop --title "feat: Your Feature Name" --body "Description"

# Wait for review and approval
```

### 4. After PR Approval - Merge to Develop

```bash
# PR merged to develop via GitHub

# Update local develop
cd /home/admin/Metrica-Fleet
git checkout develop
git pull origin develop
```

### 5. Deploying to Production

**ONLY after thorough testing on develop:**

```bash
# Create PR from develop to master
gh pr create --base master --head develop --title "release: Deploy tested changes to production"

# After master PR is merged, deploy to production
cd /home/admin/Metrica-Fleet

# Stop development services
cd overlord
docker compose down

# Switch to master branch
cd ..
git checkout master
git pull origin master

# Deploy production environment
cd overlord
docker compose pull
docker compose up -d

# Verify deployment
docker compose ps
curl http://localhost:8080/health

# Switch back to develop for continued work
cd ..
git checkout develop
```

---

## Important Rules

### DO ✅

- **Always work on `develop` branch for development**
- **Test changes thoroughly on `develop` before merging to `master`**
- **Create PRs to `develop` for review (optional for solo work)**
- **Only merge to `master` after thorough testing**
- **Stop services before switching branches**
- **Document changes in commit messages**
- **Run tests before deploying**
- **Use consistent ports** (8080, 3000, 3001)

### DON'T ❌

- **Never commit directly to master** (always merge via PR or from develop)
- **Never deploy untested code to production** (master branch)
- **Never run dev and prod simultaneously** (same ports, will conflict)
- **Never skip testing before deployment**
- **Never commit sensitive credentials** (.env files)

---

## Port Allocation

Standard ports used for all deployments:

| Service | Port | Internal Port |
|---------|------|---------------|
| API | 8080 | 8080 |
| Grafana | 3000 | 3000 |
| Dashboard | 3001 | 3001 |
| Prometheus | 9090 | 9090 |
| Alertmanager | 9093 | 9093 |
| Loki | 3100 | 3100 |
| PostgreSQL | 5432 | 5432 |

Configure in `overlord/.env`:
```bash
API_PORT=8080
GRAFANA_PORT=3000
DASHBOARD_PORT=3001
# ... etc
```

---

## Environment Configuration

### Development `.env` Template

```bash
# Development Configuration
POSTGRES_DB=fleet_dev
POSTGRES_USER=fleet_dev
POSTGRES_PASSWORD=<dev-password>

GRAFANA_ADMIN_PASSWORD=<dev-password>
API_SECRET_KEY=<dev-key>

# Development Ports
API_PORT=18080
GRAFANA_PORT=13000
DASHBOARD_PORT=13001

# Development URLs
API_URL=http://100.64.123.81:18080
GRAFANA_ROOT_URL=http://100.64.123.81:13000

# More verbose logging
LOG_LEVEL=debug
```

### Production `.env` Template

```bash
# Production Configuration
POSTGRES_DB=fleet
POSTGRES_USER=fleet
POSTGRES_PASSWORD=<prod-password>

GRAFANA_ADMIN_PASSWORD=<prod-password>
API_SECRET_KEY=<prod-key>

# Production Ports
API_PORT=8080
GRAFANA_PORT=3000
DASHBOARD_PORT=3001

# Production URLs
API_URL=http://100.64.123.81:8080
GRAFANA_ROOT_URL=http://100.64.123.81:3000

# Production logging
LOG_LEVEL=info
```

---

## Common Tasks

### Check Current Worktree Status

```bash
# List all worktrees
git worktree list

# Check current branch
git branch --show-current

# Check which files are in which worktree
ls /home/admin/Metrica-Fleet/       # Development
ls /home/admin/Metrica-Fleet-prod/  # Production
```

### Switch Between Environments

```bash
# Work on development
cd /home/admin/Metrica-Fleet

# Check production status
cd /home/admin/Metrica-Fleet-prod
```

### View Running Services

```bash
# All containers
docker ps

# Development containers only
docker ps --filter "name=fleet-dev"

# Production containers only
docker ps --filter "name=fleet-prod"
```

### Update Documentation

When updating documentation (like this file):

```bash
cd /home/admin/Metrica-Fleet
git checkout develop

# Edit documentation
nano .claude/instructions.md

# Commit
git add .claude/instructions.md
git commit -m "docs: update development workflow instructions"

# Push
git push origin develop
```

---

## Troubleshooting

### "Branch already checked out" Error

**Problem**: Trying to checkout a branch that's already in use by another worktree.

**Solution**: Each worktree must be on a different branch. Switch to a different branch or work in the appropriate worktree.

```bash
# See which branch is where
git worktree list

# Work in the correct worktree for that branch
cd /home/admin/Metrica-Fleet        # for develop
cd /home/admin/Metrica-Fleet-prod   # for production
```

### Port Already in Use

**Problem**: Docker can't start because port is already in use.

**Solution**: Check which environment is using the port and stop it.

```bash
# Check port usage
ss -tlnp | grep 8080

# Check running containers
docker ps

# Stop development
cd /home/admin/Metrica-Fleet/overlord
docker compose down

# Stop production
cd /home/admin/Metrica-Fleet-prod/overlord
docker compose down
```

### Uncommitted Changes in Wrong Worktree

**Problem**: Made changes in wrong worktree.

**Solution**: Stash and apply in correct location.

```bash
# In wrong worktree
git stash

# Switch to correct worktree
cd /home/admin/Metrica-Fleet

# Apply changes
git stash pop
```

---

## Key Files and Directories

```
Metrica-Fleet/
├── .claude/
│   └── instructions.md           # This file - workflow instructions
├── overlord/                      # Overlord deployment configuration
│   ├── .env                       # Development environment config (not committed)
│   ├── .env.example               # Template for .env
│   ├── docker-compose.yml         # Service definitions
│   ├── api/                       # Fleet API service
│   ├── dashboard/                 # Web UI (incomplete)
│   ├── grafana/                   # Monitoring dashboards
│   ├── prometheus/                # Metrics collection
│   └── scripts/                   # Deployment scripts
├── roles/                         # Device role definitions
├── common/                        # Shared components
├── scripts/                       # Utility scripts
├── templates/                     # Configuration templates
├── DEVELOPMENT_WORKFLOW.md        # Detailed worktree guide
├── DEVICE_FEASIBILITY_ASSESSMENT.md  # Device analysis
├── DEPLOYMENT_REPORT.md           # Deployment findings
├── ARCHITECTURE.md                # System architecture
├── IMPLEMENTATION.md              # Implementation guide
└── README.md                      # Project overview
```

---

## Quick Reference Commands

```bash
# Development workflow
cd /home/admin/Metrica-Fleet
git checkout develop
git pull origin develop
git checkout -b feat/new-feature
# ... make changes ...
git add .
git commit -m "feat: description"
git push origin feat/new-feature
gh pr create --base develop

# Production update
cd /home/admin/Metrica-Fleet-prod
git pull origin master
cd overlord && docker compose up -d

# Check status
git worktree list
docker ps
ss -tlnp | grep -E "8080|3000|3001"

# View logs
cd overlord
docker compose logs -f fleet-api
```

---

## Repository State

### Current Setup (2025-11-11)

- ✅ Git worktrees configured (dev + prod)
- ✅ Development workflow documented
- ✅ Device assessment complete
- ✅ Environment configuration ready
- ⏸️ Overlord deployment pending (dashboard incomplete)

### Next Steps

1. Choose dashboard approach:
   - Deploy without dashboard (use Grafana)
   - Implement simple placeholder
   - Build full React dashboard

2. Complete first deployment
3. Test device registration via API
4. Set up monitoring and alerts
5. Configure production security

---

## Additional Resources

- **Worktree Guide**: `DEVELOPMENT_WORKFLOW.md` - Complete worktree usage
- **Device Info**: `DEVICE_FEASIBILITY_ASSESSMENT.md` - Hardware/software specs
- **Deployment Report**: `DEPLOYMENT_REPORT.md` - Initial deployment findings
- **Architecture**: `ARCHITECTURE.md` - System design details
- **API Docs**: `/overlord/api/README.md` - API documentation
- **GitHub**: https://github.com/Wandeon/Metrica-Fleet

---

**Remember**: Development happens in `Metrica-Fleet/` on `develop` branch. Production updates happen in `Metrica-Fleet-prod/` from `master` branch. Both can run simultaneously without conflicts.

**Last Updated**: 2025-11-11 by Claude Code
