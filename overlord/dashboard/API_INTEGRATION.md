# Fleet Dashboard API Integration Guide

Complete guide for integrating with the Metrica Fleet API.

## Overview

The Fleet Dashboard communicates with the Fleet Management API over HTTP/REST. All API requests are authenticated using an API key passed in the `X-API-Key` header.

## Base Configuration

### API Client Setup

The API client is configured in `src/services/api.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
const API_KEY = import.meta.env.VITE_API_KEY || '';
```

### Environment Variables

```bash
# Required
VITE_API_URL=http://your-api-host:8080

# Optional (for authenticated requests)
VITE_API_KEY=your-api-key-here

# Optional (for Grafana integration)
VITE_GRAFANA_URL=http://grafana:3000
```

## API Endpoints

### Device Management

#### List All Devices
```
GET /api/v1/devices
```

**Query Parameters:**
- `role` - Filter by device role
- `status` - Filter by status (healthy, degraded, offline, error)
- `branch` - Filter by git branch
- `segment` - Filter by deployment segment
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20)

**Response:**
```json
{
  "items": [
    {
      "device_id": "pi-camera-001",
      "hostname": "camera-01",
      "role": "camera-single",
      "status": "healthy",
      "branch": "main",
      "segment": "stable",
      "ip_address": "192.168.1.100",
      "last_seen": "2025-11-11T10:30:00Z",
      "cpu_percent": 25.5,
      "memory_percent": 60.2,
      "disk_percent": 45.8
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### Get Device Details
```
GET /api/v1/devices/{device_id}
```

**Response:**
```json
{
  "device_id": "pi-camera-001",
  "hostname": "camera-01",
  "role": "camera-single",
  "status": "healthy",
  "branch": "main",
  "segment": "stable",
  "ip_address": "192.168.1.100",
  "tailscale_ip": "100.64.0.1",
  "commit_hash": "abc1234",
  "last_seen": "2025-11-11T10:30:00Z",
  "registered_at": "2025-10-01T08:00:00Z",
  "uptime_seconds": 86400,
  "cpu_percent": 25.5,
  "memory_percent": 60.2,
  "disk_percent": 45.8,
  "temperature": 55.0,
  "tags": ["production", "camera"],
  "metadata": {}
}
```

#### Register Device
```
POST /api/v1/devices/register
```

**Request Body:**
```json
{
  "device_id": "pi-camera-001",
  "hostname": "camera-01",
  "role": "camera-single",
  "branch": "main",
  "segment": "stable",
  "ip_address": "192.168.1.100",
  "tailscale_ip": "100.64.0.1",
  "tags": ["production"]
}
```

**Response:** Returns created device object

#### Update Device
```
PATCH /api/v1/devices/{device_id}
```

**Request Body:** (all fields optional)
```json
{
  "hostname": "new-hostname",
  "role": "camera-multi",
  "branch": "staging",
  "segment": "beta",
  "tags": ["updated"]
}
```

#### Delete Device
```
DELETE /api/v1/devices/{device_id}
```

**Response:** 204 No Content

#### Get Device Statistics
```
GET /api/v1/devices/statistics
```

**Response:**
```json
{
  "by_role": {
    "camera-single": 50,
    "camera-multi": 30,
    "controller": 10
  },
  "by_status": {
    "healthy": 80,
    "degraded": 5,
    "offline": 5
  },
  "by_segment": {
    "stable": 70,
    "beta": 15,
    "canary": 5
  },
  "total": 90
}
```

### Deployment Management

#### List Deployments
```
GET /api/v1/deployments
```

**Query Parameters:**
- `status` - Filter by status (pending, running, completed, failed, cancelled)
- `strategy` - Filter by strategy
- `page` - Page number
- `page_size` - Items per page

**Response:** Paginated list of deployments

#### Get Deployment Details
```
GET /api/v1/deployments/{deployment_id}
```

**Response:**
```json
{
  "deployment_id": "dep-001",
  "title": "Production Release v2.1.0",
  "description": "Latest production release",
  "strategy": "canary",
  "status": "running",
  "target_branch": "main",
  "target_commit": "abc1234",
  "target_segments": ["stable"],
  "total_devices": 50,
  "completed_devices": 25,
  "failed_devices": 2,
  "created_at": "2025-11-11T10:00:00Z",
  "started_at": "2025-11-11T10:05:00Z",
  "created_by": "admin",
  "rollback_enabled": true
}
```

#### Create Deployment
```
POST /api/v1/deployments
```

**Request Body:**
```json
{
  "title": "Production Release v2.1.0",
  "description": "Latest production release",
  "strategy": "canary",
  "target_branch": "main",
  "target_commit": "abc1234",
  "target_segments": ["stable"],
  "rollback_enabled": true,
  "auto_rollback_on_failure": false
}
```

#### Get Deployment Progress
```
GET /api/v1/deployments/{deployment_id}/progress
```

**Response:**
```json
[
  {
    "deployment_id": "dep-001",
    "device_id": "pi-camera-001",
    "status": "completed",
    "progress_percent": 100,
    "message": "Deployment successful",
    "started_at": "2025-11-11T10:05:00Z",
    "completed_at": "2025-11-11T10:10:00Z"
  }
]
```

#### Cancel Deployment
```
POST /api/v1/deployments/{deployment_id}/cancel
```

#### Rollback Deployment
```
POST /api/v1/deployments/{deployment_id}/rollback
```

### Alert Management

#### List Alerts
```
GET /api/v1/alerts
```

**Query Parameters:**
- `status` - Filter by status (firing, resolved, acknowledged)
- `severity` - Filter by severity (critical, warning, info)
- `device_id` - Filter by device
- `page` - Page number
- `page_size` - Items per page

**Response:** Paginated list of alerts

#### Get Alert Details
```
GET /api/v1/alerts/{alert_id}
```

**Response:**
```json
{
  "alert_id": "alert-001",
  "alert_name": "HighCPUUsage",
  "severity": "warning",
  "status": "firing",
  "message": "CPU usage above 80%",
  "device_id": "pi-camera-001",
  "source": "prometheus",
  "labels": {
    "severity": "warning",
    "device": "pi-camera-001"
  },
  "starts_at": "2025-11-11T10:00:00Z",
  "runbook_url": "https://docs.example.com/runbooks/high-cpu"
}
```

#### Acknowledge Alert
```
POST /api/v1/alerts/{alert_id}/acknowledge
```

**Request Body:**
```json
{
  "acknowledged_by": "admin"
}
```

#### Resolve Alert
```
POST /api/v1/alerts/{alert_id}/resolve
```

#### Silence Alert
```
POST /api/v1/alerts/{alert_id}/silence
```

**Request Body:**
```json
{
  "silence_until": "2025-11-11T12:00:00Z"
}
```

### Metrics

#### Get Fleet Metrics
```
GET /api/v1/metrics/fleet
```

**Response:**
```json
{
  "total_devices": 90,
  "healthy_devices": 80,
  "degraded_devices": 5,
  "offline_devices": 5,
  "error_devices": 0,
  "avg_cpu_percent": 30.5,
  "avg_memory_percent": 65.2,
  "avg_disk_percent": 50.1,
  "active_deployments": 2,
  "active_alerts": 3,
  "timestamp": "2025-11-11T10:30:00Z"
}
```

#### Get Device Metrics
```
GET /api/v1/metrics/devices/{device_id}
```

**Query Parameters:**
- `start_time` - Start timestamp (ISO 8601)
- `end_time` - End timestamp (ISO 8601)
- `metrics` - Comma-separated list (cpu, memory, disk, temperature)
- `interval` - Aggregation interval (1m, 5m, 15m, 1h, 1d)

## Error Handling

### Error Response Format

All API errors follow this format:

```json
{
  "error": "ValidationError",
  "message": "Invalid device ID format",
  "details": {
    "field": "device_id",
    "constraint": "must match pattern pi-*"
  }
}
```

### HTTP Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid API key
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate device ID)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

## Authentication

### API Key Header

All requests must include the API key:

```
X-API-Key: your-api-key-here
```

### Example Request

```bash
curl -X GET \
  http://localhost:8080/api/v1/devices \
  -H 'X-API-Key: your-api-key-here' \
  -H 'Content-Type: application/json'
```

## Rate Limiting

The API implements rate limiting:

- **Default**: 100 requests per minute per API key
- **Burst**: 20 requests per second

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1636646400
```

## Pagination

Paginated endpoints return:

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

## Websocket (Future)

Real-time updates via WebSocket:

```
ws://localhost:8080/api/v1/ws
```

**Planned features:**
- Real-time device status updates
- Live deployment progress
- Alert notifications

## SDK Usage

### React Query Hooks

The dashboard provides custom hooks for API access:

```typescript
import { useDevices, useDevice, useRegisterDevice } from '@/hooks/useApi';

// List devices
const { data, isLoading, error } = useDevices({ status: 'healthy' });

// Get device
const { data: device } = useDevice('pi-camera-001');

// Register device
const registerMutation = useRegisterDevice();
registerMutation.mutate(deviceData);
```

### Service Layer

Direct API access via services:

```typescript
import { deviceService } from '@/services/devices';

// Get devices
const devices = await deviceService.getDevices({ status: 'healthy' });

// Register device
const device = await deviceService.registerDevice(data);
```

## Best Practices

1. **Use React Query hooks** for automatic caching and revalidation
2. **Handle errors gracefully** with try/catch and error boundaries
3. **Implement retry logic** for transient failures
4. **Cache responses** when appropriate
5. **Use pagination** for large datasets
6. **Validate input** before sending requests
7. **Monitor rate limits** and implement backoff

## Troubleshooting

### Connection Issues

1. Check API URL is correct
2. Verify API is running: `curl http://localhost:8080/health`
3. Check CORS configuration
4. Verify firewall rules

### Authentication Issues

1. Verify API key is set in environment
2. Check API key format
3. Ensure key has required permissions
4. Check for expired keys

### Data Issues

1. Verify request format matches documentation
2. Check TypeScript types match API schema
3. Validate data before sending
4. Review API error messages

---

For more information, see the [main README](./README.md) or [API documentation](../api/README.md).
