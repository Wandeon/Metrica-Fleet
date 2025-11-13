"""
Metrica Fleet Management API
Central Overlord API for managing Pi fleet devices
"""

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import Optional, List
import structlog
from datetime import datetime, timedelta

from config import settings
from database import engine, Base, get_db
from models import Device, DeviceHeartbeat, DeviceEvent, DeviceUpdate
from schemas import (
    DeviceRegister,
    DeviceStatusUpdate,
    DeviceHeartbeatCreate,
    DeviceResponse,
    DeviceListResponse,
    DeviceConfigResponse,
    DeploymentCreate,
    DeploymentResponse,
    DeploymentReportRequest,
    DeploymentReportResponse,
    HealthResponse
)
from auth import verify_api_key
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

# Configure structured logging
logger = structlog.get_logger()

# Prometheus metrics
device_heartbeat_counter = Counter('fleet_device_heartbeats_total', 'Total device heartbeats', ['device_id', 'status'])
device_registration_counter = Counter('fleet_device_registrations_total', 'Total device registrations', ['role'])
deployment_counter = Counter('fleet_deployments_total', 'Total deployments', ['status'])
api_request_duration = Histogram('fleet_api_request_duration_seconds', 'API request duration', ['method', 'endpoint'])
active_devices_gauge = Gauge('fleet_active_devices', 'Number of active devices', ['status'])

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Fleet Management API", version=settings.VERSION)

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized")

    yield

    logger.info("Shutting down Fleet Management API")

# Create FastAPI application
app = FastAPI(
    title="Metrica Fleet Management API",
    description="Central Overlord API for managing Raspberry Pi fleet devices",
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        await db.execute(select(1))

        # Get basic stats
        device_count = await db.scalar(select(func.count(Device.device_id)))

        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version=settings.VERSION,
            database="connected",
            device_count=device_count or 0
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            version=settings.VERSION,
            database="disconnected",
            device_count=0
        )

# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

# Device registration endpoint
@app.post("/api/v1/devices/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    device_data: DeviceRegister,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Register a new device or update existing device registration"""
    logger.info("Device registration", device_id=device_data.device_id, role=device_data.role)

    # Check if device already exists
    result = await db.execute(select(Device).where(Device.device_id == device_data.device_id))
    existing_device = result.scalar_one_or_none()

    if existing_device:
        # Update existing device
        existing_device.hostname = device_data.hostname
        existing_device.role = device_data.role
        existing_device.branch = device_data.branch
        existing_device.ip_address = device_data.ip_address
        existing_device.tailscale_ip = device_data.tailscale_ip
        existing_device.agent_version = device_data.agent_version
        existing_device.last_seen = datetime.utcnow()
        existing_device.status = "healthy"
        existing_device.metadata = device_data.metadata or {}

        device = existing_device
        logger.info("Device updated", device_id=device_data.device_id)
    else:
        # Create new device
        device = Device(
            device_id=device_data.device_id,
            hostname=device_data.hostname,
            role=device_data.role,
            branch=device_data.branch or "main",
            segment=device_data.segment or "stable",
            status="healthy",
            ip_address=device_data.ip_address,
            tailscale_ip=device_data.tailscale_ip,
            agent_version=device_data.agent_version,
            last_seen=datetime.utcnow(),
            first_registered=datetime.utcnow(),
            metadata=device_data.metadata or {}
        )
        db.add(device)

        device_registration_counter.labels(role=device_data.role).inc()
        logger.info("New device registered", device_id=device_data.device_id)

        # Log registration event
        event = DeviceEvent(
            device_id=device_data.device_id,
            event_type="registration",
            severity="info",
            message=f"Device {device_data.device_id} registered",
            component="api"
        )
        db.add(event)

    await db.commit()
    await db.refresh(device)

    return device

# Device heartbeat endpoint
@app.post("/api/v1/devices/{device_id}/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
async def device_heartbeat(
    device_id: str,
    heartbeat: DeviceHeartbeatCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Receive device heartbeat"""
    logger.debug("Device heartbeat", device_id=device_id, status=heartbeat.status)

    # Get device
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Update device status
    device.last_seen = datetime.utcnow()
    device.status = heartbeat.status
    device.uptime_seconds = heartbeat.uptime_seconds
    device.cpu_usage_percent = heartbeat.cpu_percent
    device.memory_usage_percent = heartbeat.memory_percent
    device.disk_usage_percent = heartbeat.disk_percent
    device.temperature_celsius = heartbeat.temperature
    device.current_commit_hash = heartbeat.commit_hash

    # Create heartbeat record
    heartbeat_record = DeviceHeartbeat(
        device_id=device_id,
        status=heartbeat.status,
        commit_hash=heartbeat.commit_hash,
        uptime_seconds=heartbeat.uptime_seconds,
        cpu_percent=heartbeat.cpu_percent,
        memory_percent=heartbeat.memory_percent,
        disk_percent=heartbeat.disk_percent,
        temperature=heartbeat.temperature,
        ip_address=heartbeat.ip_address,
        containers_running=heartbeat.containers_running,
        containers_failed=heartbeat.containers_failed,
        metadata=heartbeat.metadata or {}
    )
    db.add(heartbeat_record)

    device_heartbeat_counter.labels(device_id=device_id, status=heartbeat.status).inc()

    await db.commit()

    return None

# Get device list
@app.get("/api/v1/devices", response_model=DeviceListResponse)
async def list_devices(
    status: Optional[str] = None,
    role: Optional[str] = None,
    segment: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """List all devices with optional filtering"""
    query = select(Device)

    # Apply filters
    filters = []
    if status:
        filters.append(Device.status == status)
    if role:
        filters.append(Device.role == role)
    if segment:
        filters.append(Device.segment == segment)

    if filters:
        query = query.where(and_(*filters))

    # Get total count
    count_query = select(func.count()).select_from(Device)
    if filters:
        count_query = count_query.where(and_(*filters))
    total = await db.scalar(count_query)

    # Get devices
    query = query.offset(skip).limit(limit).order_by(Device.device_id)
    result = await db.execute(query)
    devices = result.scalars().all()

    # Update Prometheus gauges
    for device_status in ["healthy", "degraded", "failed", "offline"]:
        count = await db.scalar(select(func.count()).select_from(Device).where(Device.status == device_status))
        active_devices_gauge.labels(status=device_status).set(count or 0)

    return DeviceListResponse(
        devices=devices,
        total=total or 0,
        skip=skip,
        limit=limit
    )

# Get specific device
@app.get("/api/v1/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get specific device details"""
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return device

# Update device status
@app.patch("/api/v1/devices/{device_id}/status")
async def update_device_status(
    device_id: str,
    status_update: DeviceStatusUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Update device status (maintenance mode, version lock, etc.)"""
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if status_update.maintenance_mode is not None:
        device.maintenance_mode = status_update.maintenance_mode
    if status_update.update_enabled is not None:
        device.update_enabled = status_update.update_enabled
    if status_update.version_lock is not None:
        device.version_lock = status_update.version_lock
    if status_update.segment is not None:
        device.segment = status_update.segment

    await db.commit()
    await db.refresh(device)

    logger.info("Device status updated", device_id=device_id, updates=status_update.dict(exclude_none=True))

    return device

# Get device events
@app.get("/api/v1/devices/{device_id}/events")
async def get_device_events(
    device_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get device event history"""
    result = await db.execute(
        select(DeviceEvent)
        .where(DeviceEvent.device_id == device_id)
        .order_by(DeviceEvent.timestamp.desc())
        .limit(limit)
    )
    events = result.scalars().all()

    return {"events": events}

# Get device configuration
@app.get("/api/v1/devices/{device_id}/config", response_model=DeviceConfigResponse)
async def get_device_config(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get device configuration"""
    logger.debug("Device config requested", device_id=device_id)

    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return DeviceConfigResponse(
        device_id=device.device_id,
        role=device.role,
        branch=device.branch,
        segment=device.segment,
        update_enabled=device.update_enabled,
        version_lock=device.version_lock,
        maintenance_mode=device.maintenance_mode,
        config=device.device_metadata or {}
    )

# Device deployment report
@app.post("/api/v1/devices/{device_id}/deployment", response_model=DeploymentReportResponse)
async def report_deployment(
    device_id: str,
    deployment: DeploymentReportRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Receive deployment status report from device"""
    logger.info("Deployment report", device_id=device_id, status=deployment.status, commit=deployment.commit_hash)

    # Get device
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Update device commit hash if successful
    if deployment.status == "success":
        device.previous_commit_hash = device.current_commit_hash
        device.current_commit_hash = deployment.commit_hash
        device.status = "healthy"
    elif deployment.status == "failed":
        device.status = "degraded"

    # Create deployment update record
    update_record = DeviceUpdate(
        device_id=device_id,
        from_commit_hash=device.previous_commit_hash,
        to_commit_hash=deployment.commit_hash,
        update_status=deployment.status,
        completed_at=datetime.utcnow() if deployment.status in ["success", "failed"] else None,
        error_message=deployment.error,
        health_check_passed=(deployment.status == "success"),
        health_check_details=deployment.deploy_metadata
    )
    db.add(update_record)

    # Log deployment event
    event = DeviceEvent(
        device_id=device_id,
        event_type="deployment",
        severity="info" if deployment.status == "success" else "error",
        message=f"Deployment {deployment.status}: {deployment.commit_hash[:8]}",
        details=deployment.deploy_metadata,
        commit_hash=deployment.commit_hash,
        component="deployment"
    )
    db.add(event)

    await db.commit()
    await db.refresh(update_record)

    deployment_counter.labels(status=deployment.status).inc()

    return DeploymentReportResponse(
        deployment_id=str(update_record.id),
        status="acknowledged",
        message=f"Deployment report received for {device_id}"
    )

# ==========================================
# Device Agent API Endpoints (Simplified Paths)
# ==========================================

# These endpoints provide simpler paths for device agents
# without the /v1/ version prefix

@app.post("/api/devices", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device_simple(
    device_data: DeviceRegister,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Register a new device (simplified path for agents)"""
    return await register_device(device_data, db, api_key)

@app.post("/api/devices/{device_id}/heartbeat", status_code=status.HTTP_200_OK)
async def device_heartbeat_simple(
    device_id: str,
    heartbeat: DeviceHeartbeatCreate,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Receive device heartbeat (simplified path for agents)"""
    await device_heartbeat(device_id, heartbeat, db, api_key)
    return {"acknowledged": True, "next_heartbeat_seconds": 30}

@app.get("/api/devices/{device_id}/config", response_model=DeviceConfigResponse)
async def get_device_config_simple(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Get device configuration (simplified path for agents)"""
    return await get_device_config(device_id, db, api_key)

@app.post("/api/devices/{device_id}/deployment", response_model=DeploymentReportResponse)
async def report_deployment_simple(
    device_id: str,
    deployment: DeploymentReportRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """Receive deployment status (simplified path for agents)"""
    return await report_deployment(device_id, deployment, db, api_key)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Metrica Fleet Management API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
