"""SQLAlchemy models for Fleet Management"""

from sqlalchemy import Column, String, Integer, Boolean, BigInteger, DateTime, Float, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.sql import func
from database import Base
import uuid


class Device(Base):
    """Device model"""
    __tablename__ = "devices"

    device_id = Column(String(64), primary_key=True)
    hostname = Column(String(255), nullable=False)
    role = Column(String(64), nullable=False)
    branch = Column(String(64), default="main")
    segment = Column(String(32), default="stable")

    # Status tracking
    status = Column(String(32), default="unknown")
    last_seen = Column(DateTime(timezone=True))
    first_registered = Column(DateTime(timezone=True), default=func.now())

    # Deployment information
    current_commit_hash = Column(String(64))
    current_version = Column(String(64))
    previous_commit_hash = Column(String(64))
    agent_version = Column(String(32))

    # System metrics
    uptime_seconds = Column(BigInteger, default=0)
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    disk_usage_percent = Column(Float)
    temperature_celsius = Column(Float)

    # Network information
    ip_address = Column(INET)
    tailscale_ip = Column(INET)
    mac_address = Column(String(17))

    # Update control
    update_enabled = Column(Boolean, default=True)
    version_lock = Column(String(64))
    maintenance_mode = Column(Boolean, default=False)

    # Metadata
    device_metadata = Column(JSONB, default={})
    labels = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class DeviceUpdate(Base):
    """Device update history"""
    __tablename__ = "device_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(64), ForeignKey("devices.device_id", ondelete="CASCADE"))

    # Update details
    from_commit_hash = Column(String(64))
    to_commit_hash = Column(String(64), nullable=False)
    update_status = Column(String(32), nullable=False)

    # Timing
    started_at = Column(DateTime(timezone=True), default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Result
    error_message = Column(Text)
    rollback_reason = Column(Text)

    # Health checks
    health_check_passed = Column(Boolean)
    health_check_details = Column(JSONB)

    created_at = Column(DateTime(timezone=True), default=func.now())


class DeviceHeartbeat(Base):
    """Device heartbeat records"""
    __tablename__ = "device_heartbeats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(64), ForeignKey("devices.device_id", ondelete="CASCADE"))

    timestamp = Column(DateTime(timezone=True), default=func.now())

    # Quick status
    status = Column(String(32), nullable=False)
    commit_hash = Column(String(64))
    uptime_seconds = Column(BigInteger)

    # Resource metrics
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)
    temperature = Column(Float)

    # Network
    ip_address = Column(INET)

    # Container status
    containers_running = Column(Integer)
    containers_failed = Column(Integer)

    heartbeat_metadata = Column(JSONB, default={})


class DeviceEvent(Base):
    """Device events and logs"""
    __tablename__ = "device_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(String(64), ForeignKey("devices.device_id", ondelete="CASCADE"))

    timestamp = Column(DateTime(timezone=True), default=func.now())
    event_type = Column(String(64), nullable=False)
    severity = Column(String(16), default="info")

    message = Column(Text, nullable=False)
    details = Column(JSONB, default={})

    # Context
    commit_hash = Column(String(64))
    component = Column(String(64))

    created_at = Column(DateTime(timezone=True), default=func.now())


class DeploymentConfig(Base):
    """Deployment configurations"""
    __tablename__ = "deployment_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False, unique=True)

    # Target specification
    branch = Column(String(64), nullable=False)
    segment = Column(String(32))
    role_filter = Column(String(64))
    device_filter = Column(JSONB)

    # Rollout strategy
    strategy = Column(String(32), default="gradual")
    batch_size = Column(Integer, default=5)
    batch_delay_seconds = Column(Integer, default=300)
    max_failures = Column(Integer, default=2)

    # Timing
    enabled = Column(Boolean, default=True)
    schedule = Column(String(128))

    # Safety
    require_health_check = Column(Boolean, default=True)
    auto_rollback = Column(Boolean, default=True)

    config_metadata = Column(JSONB, default={})

    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class DeploymentRollout(Base):
    """Deployment rollouts"""
    __tablename__ = "deployment_rollouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_config_id = Column(UUID(as_uuid=True), ForeignKey("deployment_configs.id"))

    commit_hash = Column(String(64), nullable=False)
    status = Column(String(32), default="pending")

    # Progress
    total_devices = Column(Integer, default=0)
    updated_devices = Column(Integer, default=0)
    failed_devices = Column(Integer, default=0)
    pending_devices = Column(Integer, default=0)

    # Timing
    started_at = Column(DateTime(timezone=True), default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Control
    auto_halt_triggered = Column(Boolean, default=False)
    halt_reason = Column(Text)

    rollout_metadata = Column(JSONB, default={})

    created_at = Column(DateTime(timezone=True), default=func.now())
