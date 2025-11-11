# 🗺️ Metrica Fleet - Navigation Guide for AI Agents

**Purpose**: This document is your starting point. It tells you exactly where to go based on what you need to do.

---

## 🚀 Quick Start - "Where Do I Start?"

1. **First time here?** Read the [root README.md](./README.md) for project overview
2. **Need architecture context?** Read [ARCHITECTURE.md](./ARCHITECTURE.md)
3. **Know what you need to change?** Jump to the relevant section below

---

## 📍 Navigate By Task - "I Need To..."

### 🔧 Work on the Backend API
**Location**: `overlord/api/`
**Start Here**: [overlord/api/README.md](./overlord/api/README.md)
**What's Here**: FastAPI endpoints, database models, authentication, device registration/heartbeat logic

**Common Tasks**:
- Add new API endpoint → See [overlord/api/README.md](./overlord/api/README.md#adding-endpoints)
- Modify database schema → See [overlord/api/README.md](./overlord/api/README.md#database-changes)
- Add authentication → See [overlord/api/README.md](./overlord/api/README.md#authentication)
- Debug API issues → Check logs with `overlord/scripts/logs.sh api`

**Key Files**:
- `overlord/api/main.py` - API entry point, route definitions
- `overlord/api/models.py` - Database ORM models (SQLAlchemy)
- `overlord/api/schemas.py` - Request/response validation (Pydantic)
- `overlord/api/auth.py` - Authentication logic
- `overlord/api/database.py` - Database connection and queries

---

### 🎨 Work on the Dashboard UI
**Location**: `overlord/dashboard/`
**Start Here**: [overlord/dashboard/README.md](./overlord/dashboard/README.md)
**What's Here**: Web UI for fleet management, device status, deployment controls

**Common Tasks**:
- Add new UI component → See [overlord/dashboard/README.md](./overlord/dashboard/README.md#components)
- Modify dashboard layout → Edit `overlord/dashboard/index.html`
- Add API integration → Check API endpoints in `overlord/api/main.py`

**Key Files**:
- `overlord/dashboard/index.html` - Main UI entry point
- `overlord/dashboard/package.json` - JavaScript dependencies

---

### 📊 Work on Monitoring & Metrics
**Location**: `overlord/prometheus/`, `overlord/grafana/`
**Start Here**:
- Metrics: [overlord/prometheus/README.md](./overlord/prometheus/README.md)
- Dashboards: [overlord/grafana/README.md](./overlord/grafana/README.md)

**What's Here**: Prometheus metrics, Grafana dashboards, AlertManager rules

**Common Tasks**:
- Add new metrics → See [overlord/prometheus/README.md](./overlord/prometheus/README.md#adding-metrics)
- Create dashboard → See [overlord/grafana/README.md](./overlord/grafana/README.md#dashboards)
- Configure alerts → Edit `overlord/prometheus/alerts.yml`

**Key Files**:
- `overlord/prometheus/prometheus.yml` - Scrape configuration
- `overlord/prometheus/alerts.yml` - Alert rules
- `overlord/grafana/dashboards/` - Dashboard JSON definitions

---

### 🤖 Work on Device Roles
**Location**: `roles/`
**Start Here**: [roles/README.md](./roles/README.md)
**What's Here**: Device role definitions (camera, audio, video, IoT hub, AI)

**Common Tasks**:
- Create new role → Use templates from `templates/`, see [templates/README.md](./templates/README.md)
- Modify existing role → Navigate to `roles/{role-name}/`
- Add role configuration → Edit `roles/{role-name}/docker-compose.yml`

**Key Principle**: Each role is **completely self-contained** with no cross-role dependencies

**Role Structure**:
```
roles/{role-name}/
├── docker-compose.yml     # Service definitions
├── .env.example           # Environment template
├── config/                # Role-specific configs
├── validate.sh            # Config validation
└── README.md              # Role documentation
```

---

### 📦 Work on Device Agent Scripts
**Location**: `scripts/`
**Start Here**: [scripts/README.md](./scripts/README.md)
**What's Here**: Device-side agent for pulling updates, atomic deployments, health checks

**Common Tasks**:
- Modify update logic → Edit `scripts/agent.py` (planned)
- Change deployment strategy → Edit `scripts/atomic-swap.sh` (planned)
- Add health checks → Edit `scripts/health-check.sh` (planned)

**Key Concepts**:
- **Pull-based updates**: Devices pull from Git on schedules
- **Atomic deployments**: Symlink swapping (`app_prev` ↔ `app_current` ↔ `app_next`)
- **Self-healing**: Automatic rollback to last-known-good config

---

### 🔄 Work on Deployment & Operations
**Location**: `overlord/scripts/`
**Start Here**: [overlord/README.md](./overlord/README.md#management-scripts)
**What's Here**: Deployment, backup, logging, and update scripts for the Overlord

**Common Tasks**:
- Deploy Overlord → Run `overlord/scripts/deploy.sh`
- Update services → Run `overlord/scripts/update.sh`
- View logs → Run `overlord/scripts/logs.sh [service]`
- Backup database → Run `overlord/scripts/backup.sh`

**Key Files**:
- `overlord/scripts/deploy.sh` - Initial deployment
- `overlord/scripts/update.sh` - Service updates
- `overlord/scripts/backup.sh` - Backup automation
- `overlord/scripts/logs.sh` - Log viewing

---

### 🛠️ Work on Shared Resources
**Location**: `common/`
**Start Here**: [common/README.md](./common/README.md)
**What's Here**: Shared configurations, utilities, monitoring stacks used by all roles

**Common Tasks**:
- Add shared utility → Place in `common/` and document in README
- Modify base configs → Edit templates in `common/`

---

### 📝 Create New Components from Templates
**Location**: `templates/`
**Start Here**: [templates/README.md](./templates/README.md)
**What's Here**: Boilerplate for new roles, systemd services, scripts

**Common Tasks**:
- Create new role → Copy template, customize, see [templates/README.md](./templates/README.md)

---

## 🗂️ Navigate By Component

| Component | Location | README | Purpose |
|-----------|----------|--------|---------|
| **Overlord System** | `overlord/` | [README.md](./overlord/README.md) | Central management system (VPS-01) |
| **Fleet API** | `overlord/api/` | [README.md](./overlord/api/README.md) | REST API for device management |
| **Fleet Dashboard** | `overlord/dashboard/` | [README.md](./overlord/dashboard/README.md) | Web UI for fleet management |
| **Prometheus** | `overlord/prometheus/` | [README.md](./overlord/prometheus/README.md) | Metrics aggregation & alerting |
| **Grafana** | `overlord/grafana/` | [README.md](./overlord/grafana/README.md) | Metrics visualization |
| **Loki** | `overlord/loki/` | [README.md](./overlord/loki/README.md) | Centralized log aggregation |
| **Nginx** | `overlord/nginx/` | [README.md](./overlord/nginx/README.md) | Reverse proxy & load balancer |
| **Database** | `overlord/init-db/` | [overlord/README.md](./overlord/README.md#database) | PostgreSQL schema & seed data |
| **Device Roles** | `roles/` | [README.md](./roles/README.md) | Device role definitions |
| **Device Scripts** | `scripts/` | [README.md](./scripts/README.md) | Device agent & deployment scripts |
| **Shared Resources** | `common/` | [README.md](./common/README.md) | Common configs & utilities |
| **Templates** | `templates/` | [README.md](./templates/README.md) | Boilerplate for new components |

---

## 🏗️ Architecture & Design Documents

**Essential Reading** (read these to understand system design):

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)** (896 lines)
   Detailed technical design, deployment strategies, advanced scenarios

2. **[IMPLEMENTATION.md](./IMPLEMENTATION.md)** (740 lines)
   Implementation roadmap and technical guidance

3. **[SYSTEM_ISOLATION_ASSESSMENT.md](./SYSTEM_ISOLATION_ASSESSMENT.md)** (907 lines)
   Security and isolation analysis

4. **[ENTERPRISE_RESILIENCE_AUDIT.md](./ENTERPRISE_RESILIENCE_AUDIT.md)** (1384 lines)
   Production readiness assessment

5. **[FLEET_API_SYSTEM.md](./FLEET_API_SYSTEM.md)** (129 lines)
   Fleet API system documentation

---

## ⚠️ Common Pitfalls & Guardrails

### ❌ DON'T Do These Things

1. **DON'T create cross-role dependencies**
   - Each role in `roles/` must be completely self-contained
   - See [roles/README.md](./roles/README.md#design-principles)

2. **DON'T modify the database schema without migration scripts**
   - See [overlord/api/README.md](./overlord/api/README.md#database-changes)

3. **DON'T skip validation scripts**
   - Always run `validate.sh` before deployment
   - See [roles/README.md](./roles/README.md#validation)

4. **DON'T put secrets in Git**
   - Use `.env.example` templates
   - Actual `.env` files are gitignored

5. **DON'T forget to update the CHANGELOG**
   - Document all significant changes

### ✅ DO These Things

1. **DO check existing READMEs first**
   - Most questions are answered in domain READMEs

2. **DO follow the atomic deployment pattern**
   - Use symlink swapping for updates
   - See [ARCHITECTURE.md](./ARCHITECTURE.md#atomic-deployments)

3. **DO add tests for new features**
   - See component-specific testing guidelines

4. **DO update documentation when changing behavior**
   - Keep READMEs in sync with code

---

## 🎯 Quick Reference - One-Liners

**"Where is the..."**

- **API code?** → `overlord/api/main.py`
- **Database schema?** → `overlord/init-db/01-schema.sql`
- **UI code?** → `overlord/dashboard/index.html`
- **Metrics config?** → `overlord/prometheus/prometheus.yml`
- **Alert rules?** → `overlord/prometheus/alerts.yml`
- **Deployment script?** → `overlord/scripts/deploy.sh`
- **Docker Compose?** → `overlord/docker-compose.yml`
- **Environment variables?** → `overlord/.env.example`

**"How do I..."**

- **Deploy the Overlord?** → `cd overlord && ./scripts/deploy.sh`
- **View logs?** → `cd overlord && ./scripts/logs.sh [service]`
- **Create a new role?** → Copy from `templates/`, see [templates/README.md](./templates/README.md)
- **Add API endpoint?** → See [overlord/api/README.md](./overlord/api/README.md#adding-endpoints)
- **Add dashboard?** → See [overlord/grafana/README.md](./overlord/grafana/README.md#dashboards)

---

## 📚 Additional Resources

- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - One-page cheat sheet for common operations
- **[CRITICAL_IMPLEMENTATION_ROADMAP.md](./CRITICAL_IMPLEMENTATION_ROADMAP.md)** - Implementation priorities

---

## 🆘 Still Lost?

If you can't find what you need:

1. **Check the root README.md** - High-level project overview
2. **Check ARCHITECTURE.md** - Detailed system design
3. **Check the component's README** - Most have detailed docs
4. **Search for keywords** - Use `grep -r "keyword" .` to find references
5. **Check Git history** - `git log -- path/to/file` shows change history

---

**Last Updated**: 2025-11-11
**Maintained By**: AI Agents working on Metrica Fleet
