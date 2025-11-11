# Prometheus Metrics & Alerting

**Purpose**: Metrics collection, alerting, and monitoring for the fleet management system.

**Navigation**: [← Back to Overlord](../README.md) | [← Navigation Home](../../NAVIGATION.md)

---

## 🎯 Quick Reference

**Core Files**:
- `prometheus.yml` - Scrape configuration, targets, and global settings
- `alerts.yml` - Alert rules and thresholds
- `targets/` - File-based service discovery (dynamic device targets)

**Access Points**:
- **Prometheus UI**: `http://localhost:9090`
- **Metrics Endpoint**: `http://localhost:9090/metrics`
- **API**: `http://localhost:9090/api/v1/query`

**Common Paths**:
- Prometheus data: `/var/lib/prometheus/data` (inside container)
- Config files: `/etc/prometheus/` (inside container)

---

## 📋 Common Tasks

### Adding New Metrics to the API

**Step 1: Define metric in API** (`overlord/api/main.py`)

```python
from prometheus_client import Counter, Gauge, Histogram

# Add near top of main.py with other metrics
my_new_counter = Counter(
    'fleet_my_feature_total',
    'Description of what this counts',
    ['label1', 'label2']  # Optional labels
)

my_new_gauge = Gauge(
    'fleet_current_value',
    'Description of what this measures'
)

my_new_histogram = Histogram(
    'fleet_operation_duration_seconds',
    'Time taken for operation',
    ['operation_type']
)
```

**Step 2: Instrument your code**

```python
# Increment counter
my_new_counter.labels(label1="value1", label2="value2").inc()

# Set gauge value
my_new_gauge.set(42)

# Time an operation
with my_new_histogram.labels(operation_type="update").time():
    # Your code here
    do_expensive_operation()
```

**Step 3: Verify metric appears**

```bash
# Check API metrics endpoint
curl http://localhost:8080/metrics | grep fleet_my_feature

# Query in Prometheus
# Visit http://localhost:9090 and search for "fleet_my_feature"
```

**No changes to `prometheus.yml` needed** - API metrics are auto-scraped every 15s.

---

### Adding a New Scrape Target

**For static targets** (services with known addresses):

Edit `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'my-new-service'
    static_configs:
      - targets:
          - my-service:9090
    metrics_path: /metrics  # Default, can omit
    scrape_interval: 15s    # Override global if needed
```

**For dynamic targets** (devices discovered at runtime):

Create/update `targets/pi-devices.json`:

```json
[
  {
    "targets": ["192.168.1.100:19999", "192.168.1.101:19999"],
    "labels": {
      "device_id": "pi-camera-01",
      "role": "camera-dual",
      "segment": "stable"
    }
  }
]
```

Prometheus will auto-reload this file every 60s (see `file_sd_configs` in `prometheus.yml:54-65`).

**Apply changes**:

```bash
cd overlord
docker-compose restart prometheus
# Or reload config without restart
docker-compose exec prometheus kill -HUP 1
```

---

### Creating Alert Rules

**Step 1: Add rule to `alerts.yml`**

```yaml
groups:
  - name: my_custom_alerts
    interval: 30s  # How often to evaluate these rules
    rules:
      - alert: MyCustomAlert
        expr: fleet_my_metric > 100
        for: 5m  # Alert only if true for 5 minutes
        labels:
          severity: warning  # critical, warning, info
          category: performance
        annotations:
          summary: "Short description of alert"
          description: "Detailed description. Value: {{ $value }}. Device: {{ $labels.device_id }}"
```

**Alert Severity Levels**:
- `critical` - Immediate action required (pages on-call)
- `warning` - Attention needed soon
- `info` - Informational only

**Step 2: Test the alert expression**

Visit `http://localhost:9090/graph` and test your query:
```promql
fleet_my_metric > 100
```

**Step 3: Reload Prometheus config**

```bash
cd overlord
docker-compose exec prometheus kill -HUP 1
# Or restart
docker-compose restart prometheus
```

**Step 4: Verify alert loads**

Visit `http://localhost:9090/alerts` to see your new alert rule.

---

### Common Alert Patterns

**Threshold alert**:
```yaml
- alert: HighCPU
  expr: cpu_usage_percent > 90
  for: 5m
```

**Rate-based alert**:
```yaml
- alert: HighErrorRate
  expr: rate(errors_total[5m]) > 0.1
  for: 2m
```

**Absence alert** (something stopped reporting):
```yaml
- alert: ServiceDown
  expr: up{job="my-service"} == 0
  for: 1m
```

**Comparison alert**:
```yaml
- alert: DeploymentsMuchSlower
  expr: |
    (
      avg_over_time(deployment_duration_seconds[1h])
      /
      avg_over_time(deployment_duration_seconds[24h]) offset 24h
    ) > 2
  for: 10m
```

---

### Querying Metrics

**PromQL Basics**:

```promql
# Get current value
fleet_device_cpu_usage_percent

# Filter by label
fleet_device_cpu_usage_percent{device_id="pi-camera-01"}

# Rate of change (per second)
rate(fleet_device_heartbeats_total[5m])

# Average over time
avg_over_time(fleet_device_cpu_usage_percent[1h])

# Aggregate by label
avg(fleet_device_cpu_usage_percent) by (role)

# Count devices by status
count(fleet_device_status) by (status)
```

**Useful Queries for Fleet Management**:

```promql
# Devices offline > 5 minutes
(time() - fleet_device_last_seen_timestamp_seconds) > 300

# Average CPU by role
avg(fleet_device_cpu_usage_percent) by (role)

# Device heartbeat rate
rate(fleet_device_heartbeats_total[5m])

# Failed deployments in last hour
increase(fleet_deployment_failures_total[1h])

# Device count by segment
count(fleet_device_status) by (segment)
```

**Test queries at**: `http://localhost:9090/graph`

---

## 📊 Available Metrics

### Fleet API Metrics

Defined in `overlord/api/main.py:36-40`:

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `fleet_device_heartbeats_total` | Counter | Total heartbeats received | device_id, status |
| `fleet_device_registrations_total` | Counter | Total device registrations | role |
| `fleet_deployments_total` | Counter | Total deployments | status |
| `fleet_api_request_duration_seconds` | Histogram | API request duration | method, endpoint |
| `fleet_active_devices` | Gauge | Number of active devices | status |

### Device Metrics (from Netdata)

Scraped from Pi devices via `pi-devices` job:

- `system.cpu` - CPU usage percentage
- `system.ram` - Memory usage
- `disk.space` - Disk usage
- `sensors.temperature` - Device temperature
- `docker.*` - Container metrics

### System Metrics (from Node Exporter)

VPS-01 Overlord system metrics:

- `node_cpu_seconds_total` - CPU time
- `node_memory_*` - Memory stats
- `node_disk_*` - Disk I/O
- `node_network_*` - Network stats

### Container Metrics (from cAdvisor)

Docker container metrics:

- `container_cpu_usage_seconds_total` - CPU usage per container
- `container_memory_usage_bytes` - Memory usage
- `container_network_*` - Network I/O

---

## 🚨 Existing Alert Rules

### Device Health Alerts

Located in `alerts.yml:2-92`:

| Alert | Threshold | Severity | Description |
|-------|-----------|----------|-------------|
| `DeviceOffline` | >5min no heartbeat | critical | Device hasn't reported in |
| `DeviceHighCPU` | >90% for 5min | warning | High CPU usage |
| `DeviceHighMemory` | >85% for 5min | warning | High memory usage |
| `DeviceDiskSpaceCritical` | >90% for 5min | critical | Disk almost full |
| `DeviceDiskSpaceWarning` | >80% for 10min | warning | Disk getting full |
| `DeviceHighTemperature` | >80°C for 5min | critical | Risk of thermal damage |
| `DeviceFailedState` | status=failed | critical | Device in failed state |
| `DeviceDegradedState` | status=degraded for 5min | warning | Device degraded |

### Deployment Alerts

Located in `alerts.yml:93-100`:

| Alert | Threshold | Severity | Description |
|-------|-----------|----------|-------------|
| `HighDeploymentFailureRate` | >20% failures in 30min | critical | Many deployments failing |

---

## 🔧 Configuration Details

### Scrape Configuration

**Global Settings** (`prometheus.yml:1-7`):
- `scrape_interval: 15s` - How often to scrape targets
- `scrape_timeout: 10s` - Request timeout
- `evaluation_interval: 15s` - How often to evaluate alert rules

**Jobs Configured**:

| Job Name | Target | Purpose | Path |
|----------|--------|---------|------|
| `prometheus` | localhost:9090 | Self-monitoring | prometheus.yml:23 |
| `fleet-api` | fleet-api:8080 | API metrics | prometheus.yml:29 |
| `postgres` | postgres-exporter:9187 | Database metrics | prometheus.yml:36 |
| `grafana` | grafana:3000 | Dashboard metrics | prometheus.yml:46 |
| `pi-devices` | File discovery | Device metrics | prometheus.yml:54 |
| `pushgateway` | pushgateway:9091 | Batch job metrics | prometheus.yml:68 |
| `overlord-node` | host.docker.internal:9100 | VPS system metrics | prometheus.yml:75 |
| `cadvisor` | cadvisor:8080 | Container metrics | prometheus.yml:85 |

---

### File-Based Service Discovery

**Purpose**: Dynamically add/remove device targets without restarting Prometheus.

**Configuration** (`prometheus.yml:54-65`):
```yaml
- job_name: 'pi-devices'
  file_sd_configs:
    - files:
        - '/etc/prometheus/targets/pi-devices.json'
      refresh_interval: 60s
```

**Target File Format** (`targets/pi-devices.json`):
```json
[
  {
    "targets": ["192.168.1.100:19999"],
    "labels": {
      "device_id": "pi-camera-01",
      "role": "camera-dual",
      "segment": "stable",
      "__meta_device_id": "pi-camera-01",
      "__meta_device_role": "camera-dual",
      "__meta_device_segment": "stable"
    }
  }
]
```

**Auto-generates device targets**: The Fleet API or a script should write to this file when devices register.

---

## 🛠️ Debugging & Troubleshooting

### Prometheus UI Not Loading

**Check service status**:
```bash
cd overlord
docker-compose ps prometheus
docker-compose logs prometheus
```

**Common issue**: Port 9090 already in use
```bash
# Check what's using port 9090
lsof -i :9090
# Or change port in docker-compose.yml
```

---

### Metrics Not Appearing

**Step 1: Check target is UP**

Visit `http://localhost:9090/targets` and find your target. Status should be "UP".

**If target is DOWN**:
- Check target is reachable: `curl http://target:port/metrics`
- Check Docker network: Services must be on same network
- Check firewall rules

**Step 2: Check metric name**

```bash
# List all metrics from target
curl http://target:port/metrics | grep metric_name

# Query in Prometheus
# http://localhost:9090/graph
# Search for metric name
```

**Step 3: Check scrape interval**

Metrics update every `scrape_interval` (default 15s). Wait a full interval before troubleshooting.

---

### Alert Not Firing

**Step 1: Check alert is loaded**

Visit `http://localhost:9090/alerts` - your alert should be listed.

**If not listed**:
- Check `alerts.yml` syntax (YAML is strict about indentation)
- Reload config: `docker-compose exec prometheus kill -HUP 1`
- Check logs: `docker-compose logs prometheus | grep -i alert`

**Step 2: Test the query**

Visit `http://localhost:9090/graph` and run your alert's `expr` query. Should return results.

**Step 3: Check the `for` duration**

Alert only fires if condition is true for the `for:` duration. Wait for that period.

**Step 4: Check AlertManager**

Visit `http://localhost:9093` to see if alert reached AlertManager.

---

### High Cardinality Issues

**Problem**: Too many unique label combinations causing performance issues.

**Symptoms**:
- Prometheus using excessive memory
- Slow queries
- High CPU usage

**Solution**: Reduce label cardinality
- Avoid labels with high uniqueness (timestamps, UUIDs, IPs)
- Use labels for categorization (role, segment, status), not identification
- Use `device_id` in metric name or as single label, not combined with many others

**Example - BAD**:
```python
# Creates thousands of unique series
metric.labels(device_id=id, ip=ip, timestamp=ts, session=session).inc()
```

**Example - GOOD**:
```python
# Creates manageable series
metric.labels(device_id=id, status=status).inc()
```

---

## 📚 PromQL Cheat Sheet

**Selectors**:
```promql
metric_name                          # All series for metric
metric_name{label="value"}           # Filter by label
metric_name{label=~"regex"}          # Regex match
metric_name{label!="value"}          # Not equal
```

**Aggregation**:
```promql
sum(metric_name)                     # Total
avg(metric_name)                     # Average
min(metric_name)                     # Minimum
max(metric_name)                     # Maximum
count(metric_name)                   # Count
```

**By Label**:
```promql
sum(metric_name) by (label)          # Sum per label value
avg(metric_name) without (label)     # Avg, removing label
```

**Time Functions**:
```promql
rate(counter[5m])                    # Per-second rate
increase(counter[1h])                # Total increase
avg_over_time(gauge[1h])             # Average over time
max_over_time(gauge[1h])             # Max over time
```

**Math**:
```promql
metric_a + metric_b                  # Addition
metric_a / metric_b                  # Division
metric_a > 100                       # Comparison
```

---

## 🔗 Related Documentation

- **Alert Rules**: [alerts.yml](./alerts.yml)
- **Scrape Config**: [prometheus.yml](./prometheus.yml)
- **Grafana Dashboards**: [../grafana/README.md](../grafana/README.md)
- **API Metrics**: [../api/README.md](../api/README.md#adding-prometheus-metrics)

---

## 📖 External Resources

- **Prometheus Docs**: https://prometheus.io/docs/
- **PromQL Guide**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Alert Rules**: https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
- **Best Practices**: https://prometheus.io/docs/practices/naming/

---

**Questions?** Check [NAVIGATION.md](../../NAVIGATION.md) or [overlord/README.md](../README.md)
