# Grafana Dashboards & Visualization

**Purpose**: Visual dashboards for monitoring fleet health, device metrics, and system performance.

**Navigation**: [← Back to Overlord](../README.md) | [← Navigation Home](../../NAVIGATION.md)

---

## 🎯 Quick Reference

**Core Directories**:
- `dashboards/` - Dashboard JSON definitions
- `provisioning/datasources/` - Data source configuration (Prometheus, Loki)
- `provisioning/dashboards/` - Dashboard provisioning config

**Access Points**:
- **Grafana UI**: `http://localhost:3000`
- **Default Login**: `admin` / `admin` (change on first login)
- **API**: `http://localhost:3000/api/`

**Dashboard Locations**:
- Dashboards stored in: `/var/lib/grafana/dashboards/` (inside container)
- Mounted from: `overlord/grafana/dashboards/` (host)

---

## 📋 Common Tasks

### Creating a New Dashboard

**Method 1: Via Grafana UI** (Recommended for development)

**Step 1: Create in UI**
1. Visit `http://localhost:3000`
2. Click **"+"** → **"Dashboard"**
3. Click **"Add visualization"**
4. Select **"Prometheus"** as data source
5. Write PromQL query (e.g., `fleet_device_cpu_usage_percent`)
6. Configure visualization type (graph, gauge, table, etc.)
7. Click **"Apply"**

**Step 2: Export JSON**
1. Click dashboard settings (gear icon)
2. Click **"JSON Model"**
3. Copy entire JSON

**Step 3: Save to Git**

Create file: `overlord/grafana/dashboards/my-new-dashboard.json`

```bash
cd overlord/grafana/dashboards
# Paste JSON content
cat > my-new-dashboard.json
# Paste, then Ctrl+D
```

**Step 4: Commit**

```bash
git add overlord/grafana/dashboards/my-new-dashboard.json
git commit -m "Add new dashboard for [feature]"
```

---

**Method 2: Create JSON Manually**

Create `overlord/grafana/dashboards/my-dashboard.json`:

```json
{
  "dashboard": {
    "title": "My Custom Dashboard",
    "panels": [
      {
        "id": 1,
        "type": "graph",
        "title": "Device CPU Usage",
        "targets": [
          {
            "expr": "fleet_device_cpu_usage_percent",
            "legendFormat": "{{ device_id }}"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      }
    ],
    "schemaVersion": 27,
    "version": 1
  }
}
```

**Reload dashboards**:

```bash
cd overlord
docker-compose restart grafana
```

Dashboard appears automatically in Grafana UI under "General" folder.

---

### Adding Panels to Existing Dashboard

**Step 1: Open dashboard in UI**

Visit dashboard at `http://localhost:3000/dashboards`

**Step 2: Edit dashboard**

Click **"Add panel"** button (top right)

**Step 3: Configure panel**

- **Query**: Write PromQL (e.g., `rate(fleet_api_requests_total[5m])`)
- **Visualization**: Choose type (Time series, Gauge, Stat, Bar chart, etc.)
- **Legend**: Use `{{ label }}` for dynamic labels
- **Title**: Descriptive panel title

**Common panel types**:
- **Time series**: Line graphs over time
- **Gauge**: Single value with min/max
- **Stat**: Big number display
- **Table**: Tabular data
- **Heatmap**: Density over time
- **Bar chart**: Categorical comparison

**Step 4: Export and save** (see "Creating a New Dashboard" Method 1, Steps 2-4)

---

### Useful PromQL Queries for Dashboards

**Device Status Overview**:
```promql
# Count devices by status
count(fleet_active_devices) by (status)

# Device uptime
fleet_device_uptime_seconds / 3600  # Convert to hours
```

**System Performance**:
```promql
# Average CPU by role
avg(fleet_device_cpu_usage_percent) by (role)

# Max temperature
max(fleet_device_temperature_celsius) by (device_id)

# Disk usage (top 10 devices)
topk(10, fleet_device_disk_usage_percent)
```

**API Metrics**:
```promql
# Request rate
rate(fleet_api_request_duration_seconds_count[5m])

# Request duration (p95)
histogram_quantile(0.95, rate(fleet_api_request_duration_seconds_bucket[5m]))

# Error rate
rate(fleet_api_errors_total[5m])
```

**Deployment Metrics**:
```promql
# Successful deployments over time
increase(fleet_deployments_total{status="success"}[1h])

# Deployment failure rate
rate(fleet_deployments_total{status="failed"}[5m])
  /
rate(fleet_deployments_total[5m])
```

**Alerting**:
```promql
# Currently firing alerts
ALERTS{alertstate="firing"}

# Alert count by severity
count(ALERTS{alertstate="firing"}) by (severity)
```

---

### Configuring Data Sources

**Data sources are provisioned automatically** from `provisioning/datasources/datasources.yml`.

**Existing data sources**:
- **Prometheus** - Metrics from `http://prometheus:9090`
- **Loki** - Logs from `http://loki:3100`

**To add a new data source**:

Edit `provisioning/datasources/datasources.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100

  # Add your new data source
  - name: MyNewDataSource
    type: postgres  # or influxdb, elasticsearch, etc.
    access: proxy
    url: http://my-database:5432
    database: mydb
    user: grafana
    secureJsonData:
      password: ${DATASOURCE_PASSWORD}
```

**Reload Grafana**:

```bash
cd overlord
docker-compose restart grafana
```

---

### Adding Variables to Dashboards

**Variables make dashboards dynamic** - filter by device, role, segment, etc.

**Step 1: Edit dashboard settings**

Dashboard → Settings (gear icon) → Variables → Add variable

**Step 2: Configure variable**

**Example - Device ID selector**:
- **Name**: `device_id`
- **Type**: Query
- **Data source**: Prometheus
- **Query**: `label_values(fleet_device_cpu_usage_percent, device_id)`
- **Regex**: (leave empty)
- **Multi-value**: ✓ (allow selecting multiple)
- **Include All**: ✓ (add "All" option)

**Example - Role selector**:
- **Name**: `role`
- **Query**: `label_values(fleet_device_cpu_usage_percent, role)`

**Step 3: Use variable in queries**

Instead of:
```promql
fleet_device_cpu_usage_percent{device_id="pi-camera-01"}
```

Use:
```promql
fleet_device_cpu_usage_percent{device_id=~"$device_id"}
```

Now panel updates when variable changes!

---

### Creating Alerts in Grafana

**Note**: Prefer Prometheus alerts (see [prometheus/README.md](../prometheus/README.md#creating-alert-rules)), but Grafana alerts are useful for complex logic.

**Step 1: Edit panel**

Click panel title → Edit

**Step 2: Add alert rule**

Click "Alert" tab → Create alert

**Step 3: Configure alert**

- **Name**: Alert name
- **Evaluate every**: How often to check (e.g., 1m)
- **For**: How long condition must be true (e.g., 5m)
- **Conditions**:
  - WHEN `query(A, 5m, now)` OF `metric`
  - IS ABOVE `threshold`

**Step 4: Notification**

- **Send to**: Select notification channel (configure in Alerting → Notification channels)
- **Message**: Alert message template

**Step 5: Save dashboard**

---

## 📊 Existing Dashboards

### Fleet Overview Dashboard

**File**: `dashboards/fleet-overview.json`
**Purpose**: High-level fleet health and status

**Panels**:
- Total device count
- Devices by status (healthy, degraded, failed, offline)
- Devices by role
- Recent alerts
- System resource usage trends

**Access**: `http://localhost:3000/d/fleet-overview`

---

## 🎨 Dashboard Design Best Practices

### Layout

**Dashboard grid**: 24 columns wide

**Common panel sizes**:
- **Full width**: 24 columns (w=24)
- **Half width**: 12 columns (w=12)
- **Third width**: 8 columns (w=8)
- **Quarter width**: 6 columns (w=6)

**Standard heights**:
- **Stat/Gauge**: 4-6 rows
- **Graph**: 8-10 rows
- **Table**: 10-12 rows

---

### Visualization Selection

**Use Case → Visualization Type**:

| Use Case | Best Visualization |
|----------|-------------------|
| Single current value | Stat or Gauge |
| Trend over time | Time series (line graph) |
| Multiple metrics comparison | Bar chart or Table |
| Distribution/density | Heatmap |
| Geographic data | Geomap |
| Percentage/progress | Gauge or Bar gauge |
| Top N items | Table with sorting |
| Status indicators | Stat with thresholds |

---

### Color Thresholds

**Apply consistent coloring**:

```
Green (Good):     0-70%
Yellow (Warning): 70-85%
Orange (Alert):   85-95%
Red (Critical):   95-100%
```

**Configure in panel**:
- Edit panel → Field → Thresholds
- Add steps: 70 (yellow), 85 (orange), 95 (red)

---

### Units

**Configure appropriate units**:

- **Percentage**: 0-100 → Unit: "percent (0-100)"
- **Bytes**: → Unit: "bytes (IEC)" (shows KB, MB, GB)
- **Duration**: → Unit: "seconds (s)"
- **Temperature**: → Unit: "Celsius (°C)"
- **Rate**: → Unit: "requests/sec (reqps)"

**Set in panel**: Edit → Field → Standard options → Unit

---

## 🛠️ Debugging & Troubleshooting

### Dashboard Not Showing Data

**Step 1: Check data source**

Dashboard settings → Variables → Check data source is "Prometheus" or "Loki"

**Step 2: Test query**

- Edit panel
- Check "Query inspector" (bottom of panel editor)
- Should show data returned
- If no data, test query in Prometheus UI (`http://localhost:9090/graph`)

**Step 3: Check time range**

- Dashboard time range (top right) should include period with data
- Try "Last 15 minutes" or "Last 1 hour"

**Step 4: Check Prometheus targets**

Visit `http://localhost:9090/targets` - ensure scrape target is UP

---

### Grafana Not Starting

**Check logs**:
```bash
cd overlord
docker-compose logs grafana
```

**Common issues**:
- **Permission denied**: Check volume permissions
  ```bash
  sudo chown -R 472:472 overlord/grafana
  ```
- **Port conflict**: Port 3000 already in use
  ```bash
  lsof -i :3000
  # Change port in docker-compose.yml if needed
  ```

---

### Can't Login

**Reset admin password**:

```bash
cd overlord
docker-compose exec grafana grafana-cli admin reset-admin-password newpassword
```

**Default credentials** (if not changed):
- Username: `admin`
- Password: `admin`

---

### Dashboard Changes Not Persisting

**Problem**: Changes made in UI are lost after restart.

**Cause**: Dashboard is provisioned from JSON file (read-only in UI).

**Solution**:
1. Export dashboard JSON from UI
2. Update file in `overlord/grafana/dashboards/`
3. Restart Grafana to reload

**OR**: Create new dashboard (not provisioned) for experimenting, then export when done.

---

### Slow Dashboard Loading

**Causes**:
- Too many panels (> 20)
- High-cardinality queries (millions of series)
- Long time ranges (> 24h with 15s interval)

**Solutions**:
- Reduce panels per dashboard
- Use dashboard variables to filter data
- Increase scrape interval for less important metrics
- Use recording rules in Prometheus for expensive queries

---

## 🔧 Advanced Features

### Dashboard Links

**Add links to other dashboards or external resources**:

Dashboard settings → Links → Add link

**Example - Link to device detail**:
- **Type**: Dashboard
- **Title**: Device Details
- **URL**: `/d/device-detail?var-device_id=${device_id}`

---

### Annotations

**Mark events on graphs** (deployments, incidents, etc.):

Dashboard settings → Annotations → Add annotation

**Example - Mark deployments**:
- **Name**: Deployments
- **Data source**: Prometheus
- **Query**: `changes(fleet_deployments_total[1m]) > 0`
- **Tag field**: deployment

Annotations appear as vertical lines on time series panels.

---

### Templating with Repeating Panels

**Automatically create panel for each variable value**:

1. Create panel with variable in query: `metric{device_id="$device_id"}`
2. Edit panel → Repeat options
3. Select variable: `device_id`
4. Save

Grafana creates one panel per device automatically!

---

### Playlists

**Cycle through dashboards automatically** (e.g., for wall displays):

Dashboards → Playlists → New playlist

Add dashboards and set interval (e.g., 30 seconds).

Start playlist for rotating display.

---

## 📚 Dashboard JSON Structure

**Minimal dashboard structure**:

```json
{
  "dashboard": {
    "title": "Dashboard Title",
    "uid": "unique-id",
    "tags": ["fleet", "devices"],
    "timezone": "browser",
    "panels": [],
    "templating": {
      "list": []
    },
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "refresh": "30s",
    "schemaVersion": 27,
    "version": 1
  }
}
```

**Panel structure**:

```json
{
  "id": 1,
  "type": "timeseries",
  "title": "Panel Title",
  "gridPos": {
    "h": 8,
    "w": 12,
    "x": 0,
    "y": 0
  },
  "targets": [
    {
      "expr": "prometheus_query",
      "refId": "A",
      "legendFormat": "{{ label }}"
    }
  ],
  "options": {},
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {"value": 0, "color": "green"},
          {"value": 70, "color": "yellow"},
          {"value": 85, "color": "orange"},
          {"value": 95, "color": "red"}
        ]
      }
    }
  }
}
```

---

## 🔗 Related Documentation

- **Prometheus Queries**: [../prometheus/README.md](../prometheus/README.md#querying-metrics)
- **API Metrics**: [../api/README.md](../api/README.md#adding-prometheus-metrics)
- **Loki Logs**: [../loki/README.md](../loki/README.md) (if exists)
- **Dashboard Files**: [dashboards/](./dashboards/)

---

## 📖 External Resources

- **Grafana Docs**: https://grafana.com/docs/grafana/latest/
- **Dashboard Examples**: https://grafana.com/grafana/dashboards/
- **Panel Plugins**: https://grafana.com/grafana/plugins/
- **PromQL Guide**: https://prometheus.io/docs/prometheus/latest/querying/basics/

---

**Questions?** Check [NAVIGATION.md](../../NAVIGATION.md) or [overlord/README.md](../README.md)
