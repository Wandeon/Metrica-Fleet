# Quick Reference - Metrica Fleet

**One-page cheat sheet for common operations. For details, see [NAVIGATION.md](./NAVIGATION.md)**

---

## 🗺️ Where Is Everything?

| Component | Location | README |
|-----------|----------|--------|
| **API** | `overlord/api/main.py` | [API README](overlord/api/README.md) |
| **Database Schema** | `overlord/init-db/01-schema.sql` | [Overlord README](overlord/README.md) |
| **Dashboard UI** | `overlord/dashboard/index.html` | [Dashboard README](overlord/dashboard/README.md) |
| **Metrics Config** | `overlord/prometheus/prometheus.yml` | [Prometheus README](overlord/prometheus/README.md) |
| **Alert Rules** | `overlord/prometheus/alerts.yml` | [Prometheus README](overlord/prometheus/README.md) |
| **Grafana Dashboards** | `overlord/grafana/dashboards/` | [Grafana README](overlord/grafana/README.md) |
| **Device Roles** | `roles/{role-name}/` | [Roles README](roles/README.md) |
| **Templates** | `templates/` | [Templates README](templates/README.md) |

---

## 🚀 Common Commands

### Overlord Management

```bash
# Deploy Overlord
cd overlord && ./scripts/deploy.sh

# View logs
cd overlord && ./scripts/logs.sh [api|dashboard|prometheus|grafana|postgres]

# Update services
cd overlord && ./scripts/update.sh

# Stop all services
cd overlord && ./scripts/stop.sh

# Restart specific service
cd overlord && docker-compose restart [service-name]
```

---

### API Development

```bash
# Start API
cd overlord && docker-compose up api

# Watch API logs
cd overlord && docker-compose logs -f api

# Test endpoint
curl -H "X-API-Key: your-key" http://localhost:8080/api/v1/devices

# Access API docs
open http://localhost:8080/docs
```

**Add endpoint**: Edit `overlord/api/main.py` → Add route → Restart API

**Add model**: Edit `overlord/api/models.py` → Add class → Update schema SQL

**Add schema**: Edit `overlord/api/schemas.py` → Add Pydantic model

---

### Monitoring

```bash
# Access Prometheus
open http://localhost:9090

# Access Grafana
open http://localhost:3000
# Default: admin/admin

# Reload Prometheus config
cd overlord && docker-compose exec prometheus kill -HUP 1

# Test PromQL query
curl 'http://localhost:9090/api/v1/query?query=fleet_device_cpu_usage_percent'
```

**Add metric**: Edit `overlord/api/main.py` → Define Counter/Gauge/Histogram → Use in code

**Add alert**: Edit `overlord/prometheus/alerts.yml` → Add rule → Reload Prometheus

**Add dashboard**: Create in Grafana UI → Export JSON → Save to `overlord/grafana/dashboards/`

---

### Database

```bash
# Access PostgreSQL
cd overlord && docker-compose exec postgres psql -U fleet -d fleet_db

# Run SQL file
cd overlord && docker-compose exec -T postgres psql -U fleet -d fleet_db < init-db/01-schema.sql

# Backup database
cd overlord && ./scripts/backup.sh

# Fresh database (DEV ONLY - deletes all data!)
cd overlord && docker-compose down -v && docker-compose up -d
```

---

## 📝 Code Snippets

### Add API Endpoint

**1. Schema** (`overlord/api/schemas.py`):
```python
class MyRequest(BaseModel):
    field: str

class MyResponse(BaseModel):
    result: str
    created_at: datetime
    class Config:
        from_attributes = True
```

**2. Route** (`overlord/api/main.py`):
```python
@app.post("/api/v1/my-endpoint", response_model=MyResponse)
async def my_endpoint(
    data: MyRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    logger.info("My endpoint", field=data.field)
    # Your logic
    return result
```

---

### Add Prometheus Metric

**Define** (`overlord/api/main.py` - top of file):
```python
my_counter = Counter('fleet_my_metric_total', 'Description', ['label'])
```

**Use** (in endpoint):
```python
my_counter.labels(label="value").inc()
```

**Query** (Prometheus UI):
```promql
fleet_my_metric_total
rate(fleet_my_metric_total[5m])
```

---

### Add Alert Rule

**Edit** `overlord/prometheus/alerts.yml`:
```yaml
- alert: MyAlert
  expr: metric_name > threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Alert fired"
    description: "Value: {{ $value }}"
```

**Reload**: `docker-compose exec prometheus kill -HUP 1`

---

### Query Database

**In API endpoint**:
```python
# Get one
result = await db.execute(select(Device).where(Device.device_id == id))
device = result.scalar_one_or_none()

# Get many
result = await db.execute(select(Device).where(Device.status == "healthy"))
devices = result.scalars().all()

# Count
count = await db.scalar(select(func.count()).select_from(Device))

# Create
new_device = Device(device_id="test", hostname="test")
db.add(new_device)
await db.commit()
await db.refresh(new_device)

# Update
device.status = "offline"
await db.commit()
```

---

## 🚨 Critical Don'ts

❌ **DON'T** create cross-role dependencies in `roles/`
❌ **DON'T** modify database schema without migration scripts
❌ **DON'T** commit secrets (use `.env.example` templates)
❌ **DON'T** skip `validate.sh` scripts before deployment
❌ **DON'T** use `docker-compose down -v` in production (deletes data!)

---

## ✅ Always Do

✅ **DO** check [NAVIGATION.md](./NAVIGATION.md) when lost
✅ **DO** read component README before modifying
✅ **DO** test API endpoints with `/docs` Swagger UI
✅ **DO** use structured logging: `logger.info("msg", key=value)`
✅ **DO** add Prometheus metrics for new features
✅ **DO** follow atomic deployment pattern (symlink swapping)

---

## 🎯 File Path Quick Search

**"Where do I find..."**

| What | Path |
|------|------|
| API routes | `overlord/api/main.py` |
| Database models | `overlord/api/models.py` |
| Request/response schemas | `overlord/api/schemas.py` |
| Database schema | `overlord/init-db/01-schema.sql` |
| Docker Compose | `overlord/docker-compose.yml` |
| Environment variables | `overlord/.env.example` |
| API config | `overlord/api/config.py` |
| Prometheus config | `overlord/prometheus/prometheus.yml` |
| Alert rules | `overlord/prometheus/alerts.yml` |
| Grafana dashboards | `overlord/grafana/dashboards/*.json` |
| Deployment script | `overlord/scripts/deploy.sh` |
| Logs script | `overlord/scripts/logs.sh` |

---

## 🔍 Useful PromQL Queries

```promql
# Device count by status
count(fleet_active_devices) by (status)

# Average CPU by role
avg(fleet_device_cpu_usage_percent) by (role)

# API request rate
rate(fleet_api_request_duration_seconds_count[5m])

# Devices offline > 5 min
(time() - fleet_device_last_seen_timestamp_seconds) > 300

# Top 10 CPU usage
topk(10, fleet_device_cpu_usage_percent)

# Deployment success rate
rate(fleet_deployments_total{status="success"}[1h])
  /
rate(fleet_deployments_total[1h])
```

---

## 🆘 Troubleshooting Quick Checks

| Problem | Check |
|---------|-------|
| API not responding | `docker-compose ps api` → `docker-compose logs api` |
| Database connection failed | `docker-compose ps postgres` → Check `.env` credentials |
| Metrics not appearing | `http://localhost:9090/targets` → Ensure target is UP |
| Dashboard no data | Check time range → Test query in Prometheus UI |
| Alert not firing | `http://localhost:9090/alerts` → Check `for:` duration |
| Can't login to Grafana | Default: `admin`/`admin` → Reset: `grafana-cli admin reset-admin-password` |

---

## 📚 Essential Reading (in order)

1. **[NAVIGATION.md](./NAVIGATION.md)** - Start here when lost
2. **[README.md](./README.md)** - Project overview
3. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System design (896 lines)
4. **Component READMEs** - Detailed guides for each component

---

## 🔗 URLs

| Service | URL | Default Creds |
|---------|-----|---------------|
| API Docs | http://localhost:8080/docs | API key required |
| API Health | http://localhost:8080/health | None |
| Prometheus | http://localhost:9090 | None |
| Grafana | http://localhost:3000 | admin/admin |
| AlertManager | http://localhost:9093 | None |

---

**Last Updated**: 2025-11-11
