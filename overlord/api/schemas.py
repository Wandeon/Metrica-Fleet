"""Pydantic schemas for API request/response validation"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class DeviceRegister(BaseModel):
    """Device registration schema"""
    device_id: str = Field(..., min_length=1, max_length=64)
    hostname: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=64)
    branch: Optional[str] = Field(default="main", max_length=64)
    segment: Optional[str] = Field(default="stable", max_length=32)
    ip_address: Optional[str] = None
    tailscale_ip: Optional[str] = None
    agent_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceHeartbeatCreate(BaseModel):
    """Device heartbeat schema"""
    status: str = Field(..., max_length=32)
    commit_hash: Optional[str] = None
    uptime_seconds: Optional[int] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    temperature: Optional[float] = None
    ip_address: Optional[str] = None
    containers_running: Optional[int] = None
    containers_failed: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceStatusUpdate(BaseModel):
    """Device status update schema"""
    maintenance_mode: Optional[bool] = None
    update_enabled: Optional[bool] = None
    version_lock: Optional[str] = None
    segment: Optional[str] = None


class DeviceResponse(BaseModel):
    """Device response schema"""
    device_id: str
    hostname: str
    role: str
    branch: str
    segment: str
    status: str
    last_seen: Optional[datetime] = None
    first_registered: datetime
    current_commit_hash: Optional[str] = None
    agent_version: Optional[str] = None
    uptime_seconds: Optional[int] = None
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    disk_usage_percent: Optional[float] = None
    temperature_celsius: Optional[float] = None
    ip_address: Optional[str] = None
    tailscale_ip: Optional[str] = None
    update_enabled: bool
    maintenance_mode: bool
    version_lock: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """Device list response schema"""
    devices: List[DeviceResponse]
    total: int
    skip: int
    limit: int


class DeploymentCreate(BaseModel):
    """Deployment creation schema"""
    config_id: str
    commit_hash: str
    target_devices: Optional[List[str]] = None


class DeploymentResponse(BaseModel):
    """Deployment response schema"""
    id: str
    commit_hash: str
    status: str
    total_devices: int
    updated_devices: int
    failed_devices: int
    pending_devices: int
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str
    timestamp: datetime
    version: str
    database: str
    device_count: int
