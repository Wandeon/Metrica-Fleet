# Fleet Management API

**Purpose**: FastAPI backend for managing Raspberry Pi fleet devices. Handles device registration, heartbeats, status updates, and metrics.

**Navigation**: [← Back to Overlord](../README.md) | [← Navigation Home](../../NAVIGATION.md)

---

## 🎯 Quick Reference

**Core Files**:
- `main.py` - API routes, endpoints, lifespan management
- `models.py` - SQLAlchemy database models
- `schemas.py` - Pydantic request/response validation
- `auth.py` - API key authentication
- `database.py` - Database connection & session management
- `config.py` - Configuration management

**API Base URL**: `http://localhost:8080` (inside Docker network)

**Public Endpoints**:
- `GET /health` - Health check (no auth required)
- `GET /metrics` - Prometheus metrics (no auth required)
- `GET /docs` - OpenAPI/Swagger docs (no auth required)

**Protected Endpoints** (require `X-API-Key` header):
- `POST /api/v1/devices/register` - Register/update device
- `POST /api/v1/devices/{device_id}/heartbeat` - Device heartbeat
- `GET /api/v1/devices` - List devices (with filtering)
- `GET /api/v1/devices/{device_id}` - Get device details
- `PATCH /api/v1/devices/{device_id}/status` - Update device status
- `GET /api/v1/devices/{device_id}/events` - Get device event history

---

## 📋 Common Tasks

### Adding a New Endpoint

**Step 1: Define the Pydantic schema** in `schemas.py`

```python
class NewFeatureRequest(BaseModel):
    """Request schema for new feature"""
    field_name: str = Field(..., max_length=255)
    optional_field: Optional[int] = None

class NewFeatureResponse(BaseModel):
    """Response schema for new feature"""
    id: str
    result: str
    created_at: datetime

    class Config:
        from_attributes = True
```

**Step 2: Add the route** in `main.py`

```python
@app.post("/api/v1/new-feature", response_model=NewFeatureResponse)
async def new_feature(
    request_data: NewFeatureRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Describe what this endpoint does"""
    logger.info("New feature called", field=request_data.field_name)

    # Your logic here
    # ...

    return response_object
```

**Step 3: Add Prometheus metrics** (if needed)

```python
# At the top of main.py with other metrics
new_feature_counter = Counter('fleet_new_feature_total', 'Total new feature calls')

# In your endpoint
new_feature_counter.inc()
```

**Step 4: Test the endpoint**

```bash
# From host machine
curl -X POST "http://localhost:8080/api/v1/new-feature" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"field_name": "test"}'
```

**Step 5: Check the auto-generated docs**

Visit `http://localhost:8080/docs` to see your new endpoint in Swagger UI.

---

### Database Changes

**Adding a New Column to Existing Model**

**Step 1: Modify the model** in `models.py`

```python
class Device(Base):
    __tablename__ = "devices"

    # ... existing columns ...

    # Add your new column
    new_field = Column(String(128), nullable=True)
```

**Step 2: Create migration script** in `overlord/init-db/03-add-new-field.sql`

```sql
-- Add new field to devices table
ALTER TABLE devices ADD COLUMN new_field VARCHAR(128);

-- Add index if needed
CREATE INDEX idx_devices_new_field ON devices(new_field);
```

**Step 3: Recreate the database** (development only!)

```bash
cd overlord
docker-compose down -v  # WARNING: Deletes all data
docker-compose up -d postgres
docker-compose up -d api
```

**For production**: Use Alembic for proper migrations (see [Production Migrations](#production-migrations) below)

---

**Creating a New Model**

**Step 1: Add model class** in `models.py`

```python
class NewTable(Base):
    """Description of new table"""
    __tablename__ = "new_table"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(64), ForeignKey("devices.device_id", ondelete="CASCADE"))

    # Your fields
    field_name = Column(String(255), nullable=False)
    count = Column(Integer, default=0)
    metadata = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
```

**Step 2: Add schema** in `schemas.py`

```python
class NewTableCreate(BaseModel):
    """Creation schema"""
    device_id: str
    field_name: str
    count: Optional[int] = 0

class NewTableResponse(BaseModel):
    """Response schema"""
    id: str
    device_id: str
    field_name: str
    count: int
    created_at: datetime

    class Config:
        from_attributes = True
```

**Step 3: Import in main.py** and use in endpoints

```python
from models import Device, DeviceHeartbeat, DeviceEvent, DeviceUpdate, NewTable
```

---

### Authentication

**How Authentication Works**:

1. API expects `X-API-Key` header on all protected endpoints
2. Key is verified by `verify_api_key()` dependency from `auth.py`
3. Configure valid keys in `overlord/.env`:

```bash
FLEET_API_KEY=your-secure-api-key-here
FLEET_ADMIN_API_KEY=admin-key-with-more-privileges
```

**Using Authentication in Endpoints**:

```python
@app.get("/api/v1/protected")
async def protected_route(
    api_key: str = Depends(verify_api_key)  # Add this dependency
):
    """This route requires authentication"""
    return {"message": "You're authenticated!"}
```

**Skipping Authentication** (public endpoints only):

```python
@app.get("/api/v1/public")
async def public_route():
    """This route does NOT require authentication"""
    return {"message": "Public access"}
```

---

### Working with the Database

**Getting a Database Session**:

```python
@app.get("/api/v1/example")
async def example_route(
    db: AsyncSession = Depends(get_db)  # Inject DB session
):
    """Endpoint with database access"""
    # Use the db session here
    result = await db.execute(select(Device))
    devices = result.scalars().all()
    return {"devices": devices}
```

**Querying Data**:

```python
# Get single device
result = await db.execute(
    select(Device).where(Device.device_id == "pi-camera-01")
)
device = result.scalar_one_or_none()

if not device:
    raise HTTPException(status_code=404, detail="Device not found")

# Get multiple devices with filters
result = await db.execute(
    select(Device)
    .where(Device.role == "camera-dual")
    .where(Device.status == "healthy")
    .order_by(Device.last_seen.desc())
    .limit(10)
)
devices = result.scalars().all()

# Count devices
count = await db.scalar(
    select(func.count()).select_from(Device).where(Device.status == "healthy")
)
```

**Creating Records**:

```python
# Create new device
new_device = Device(
    device_id="pi-camera-02",
    hostname="pi-camera-02.local",
    role="camera-dual",
    branch="main",
    status="healthy"
)
db.add(new_device)
await db.commit()
await db.refresh(new_device)  # Get updated fields like created_at

return new_device
```

**Updating Records**:

```python
# Get existing record
result = await db.execute(select(Device).where(Device.device_id == device_id))
device = result.scalar_one_or_none()

# Modify fields
device.status = "offline"
device.last_seen = datetime.utcnow()

# Commit changes
await db.commit()
await db.refresh(device)

return device
```

**Deleting Records**:

```python
result = await db.execute(select(Device).where(Device.device_id == device_id))
device = result.scalar_one_or_none()

if device:
    await db.delete(device)
    await db.commit()
```

---

### Adding Prometheus Metrics

**Define metric at module level** in `main.py`:

```python
# Near the top with other metrics
my_counter = Counter('fleet_my_feature_total', 'Description', ['label1', 'label2'])
my_gauge = Gauge('fleet_my_value', 'Current value of something')
my_histogram = Histogram('fleet_operation_duration_seconds', 'Operation duration', ['operation'])
```

**Use metrics in endpoints**:

```python
@app.post("/api/v1/my-endpoint")
async def my_endpoint():
    # Increment counter
    my_counter.labels(label1="value1", label2="value2").inc()

    # Set gauge value
    my_gauge.set(42)

    # Time operation
    with my_histogram.labels(operation="my_operation").time():
        # Your code here
        pass

    return {"status": "ok"}
```

**Verify metrics** at `http://localhost:8080/metrics`

---

### Logging

**Structured logging with context**:

```python
from structlog import get_logger

logger = get_logger()

# Log with context
logger.info("Device registered", device_id=device_id, role=role, ip=ip_address)
logger.warning("High temperature", device_id=device_id, temp=temperature)
logger.error("Database connection failed", error=str(e), retry_count=3)
```

**Log levels**:
- `logger.debug()` - Verbose debugging info
- `logger.info()` - Normal operations
- `logger.warning()` - Something unexpected but handled
- `logger.error()` - Errors that need attention

**Logs are collected by**:
- Docker logs: `docker-compose logs -f api`
- Loki (centralized): Check Grafana

---

## 📊 Data Models

### Device Model (Primary)

**Table**: `devices`
**Purpose**: Track all fleet devices and their current state

**Key Fields**:
- `device_id` (PK) - Unique device identifier
- `hostname` - Device hostname
- `role` - Device role (camera-dual, audio-player, etc.)
- `branch` - Git branch device follows
- `segment` - Deployment segment (stable, canary, beta)
- `status` - Current status (healthy, degraded, failed, offline)
- `last_seen` - Last heartbeat timestamp
- `current_commit_hash` - Currently deployed Git commit
- `maintenance_mode` - Whether device is in maintenance
- `update_enabled` - Whether device can auto-update
- `version_lock` - Lock device to specific version
- `metadata` - JSONB for flexible data

**Location**: `models.py:10-55`

---

### DeviceHeartbeat Model

**Table**: `device_heartbeats`
**Purpose**: Store device heartbeat history for monitoring

**Key Fields**:
- `device_id` (FK) - Device identifier
- `status` - Status at heartbeat time
- `cpu_percent`, `memory_percent`, `disk_percent` - Resource usage
- `temperature` - Device temperature
- `containers_running`, `containers_failed` - Docker status

**Location**: `models.py:85-113`

---

### DeviceEvent Model

**Table**: `device_events`
**Purpose**: Store device events (registration, errors, updates)

**Key Fields**:
- `device_id` (FK) - Device identifier
- `event_type` - Event type (registration, update, error, etc.)
- `severity` - Severity level (info, warning, error)
- `message` - Event description
- `details` - JSONB for event-specific data

**Location**: `models.py:115-133`

---

### DeviceUpdate Model

**Table**: `device_updates`
**Purpose**: Track update history and rollback information

**Key Fields**:
- `device_id` (FK) - Device identifier
- `from_commit_hash`, `to_commit_hash` - Version transition
- `update_status` - Status (success, failed, rolled_back)
- `error_message` - Error details if failed
- `health_check_passed` - Whether health checks passed

**Location**: `models.py:57-83`

---

## 🚨 Common Issues & Debugging

### "Database connection failed"

**Check database status**:
```bash
cd overlord
docker-compose ps postgres
docker-compose logs postgres
```

**Verify connection string**:
Check `overlord/.env` has correct `POSTGRES_*` variables

---

### "401 Unauthorized" on API calls

**Verify API key**:
1. Check `overlord/.env` has `FLEET_API_KEY` set
2. Ensure you're passing `X-API-Key` header
3. Restart API: `docker-compose restart api`

**Test authentication**:
```bash
curl -H "X-API-Key: your-key" http://localhost:8080/api/v1/devices
```

---

### "422 Validation Error"

**Cause**: Request body doesn't match Pydantic schema

**Debug**:
1. Check request matches schema in `schemas.py`
2. Check API docs at `http://localhost:8080/docs`
3. Enable request logging:

```python
@app.middleware("http")
async def log_requests(request, call_next):
    body = await request.body()
    logger.info("Request", path=request.url.path, body=body)
    response = await call_next(request)
    return response
```

---

### Database Migration Failed

**Fresh start** (development only):
```bash
cd overlord
docker-compose down -v  # Deletes all data!
docker-compose up -d postgres
# Wait 5 seconds for postgres to start
docker-compose up -d api
```

**Check migration logs**:
```bash
docker-compose logs api | grep -i "migration\|database"
```

---

## 🔧 Development Workflow

### Running the API Locally

**Start full stack**:
```bash
cd overlord
docker-compose up -d
```

**Start only API** (for development):
```bash
cd overlord
docker-compose up api
```

**Watch logs**:
```bash
cd overlord/scripts
./logs.sh api
```

---

### Testing Endpoints

**Using curl**:
```bash
# Health check
curl http://localhost:8080/health

# Register device
curl -X POST "http://localhost:8080/api/v1/devices/register" \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test-device-01",
    "hostname": "test-01.local",
    "role": "camera-dual",
    "branch": "main",
    "ip_address": "192.168.1.100"
  }'

# List devices
curl -H "X-API-Key: dev-api-key" "http://localhost:8080/api/v1/devices"

# Get specific device
curl -H "X-API-Key: dev-api-key" "http://localhost:8080/api/v1/devices/test-device-01"
```

**Using Swagger UI**:
Visit `http://localhost:8080/docs` and click "Authorize" to add your API key

---

### Hot Reload During Development

The API container uses `uvicorn --reload`, so code changes are automatically picked up.

**To apply changes**:
1. Edit files in `overlord/api/`
2. Save the file
3. Uvicorn automatically reloads

**If changes don't apply**:
```bash
cd overlord
docker-compose restart api
```

---

## 🏗️ Architecture Notes

### Request Flow

```
Client Request
    ↓
Nginx (port 80/443)
    ↓
API Container (port 8080)
    ↓
FastAPI Router
    ↓
Dependency Injection (Auth, DB)
    ↓
Route Handler
    ↓
Database Query (PostgreSQL)
    ↓
Response Serialization (Pydantic)
    ↓
Client Response
```

### Async/Await Pattern

All endpoints use `async def` and `await` for database operations:

```python
@app.get("/api/v1/devices")
async def list_devices(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Device))  # await required!
    devices = result.scalars().all()
    return devices
```

**Why**: Allows API to handle multiple requests concurrently without blocking

---

## 📚 Related Documentation

- **Database Schema**: [overlord/init-db/01-schema.sql](../init-db/01-schema.sql)
- **API Configuration**: [overlord/.env.example](../.env.example)
- **Deployment Guide**: [overlord/DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
- **Architecture**: [ARCHITECTURE.md](../../ARCHITECTURE.md)

---

## 🔗 External References

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Async**: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Pydantic**: https://docs.pydantic.dev/

---

**Questions?** Check [NAVIGATION.md](../../NAVIGATION.md) or [overlord/README.md](../README.md)
