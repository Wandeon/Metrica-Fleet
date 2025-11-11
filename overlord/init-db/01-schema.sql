-- Metrica Fleet Database Schema
-- Fleet Management and Device Status Tracking

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Devices table: Core device registry
CREATE TABLE devices (
    device_id VARCHAR(64) PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL,
    role VARCHAR(64) NOT NULL,
    branch VARCHAR(64) DEFAULT 'main',
    segment VARCHAR(32) DEFAULT 'stable', -- canary, beta, stable

    -- Status tracking
    status VARCHAR(32) DEFAULT 'unknown', -- unknown, healthy, degraded, failed, offline
    last_seen TIMESTAMP WITH TIME ZONE,
    first_registered TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Deployment information
    current_commit_hash VARCHAR(64),
    current_version VARCHAR(64),
    previous_commit_hash VARCHAR(64),
    agent_version VARCHAR(32),

    -- System metrics
    uptime_seconds BIGINT DEFAULT 0,
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_percent DECIMAL(5,2),
    disk_usage_percent DECIMAL(5,2),
    temperature_celsius DECIMAL(5,2),

    -- Network information
    ip_address INET,
    tailscale_ip INET,
    mac_address VARCHAR(17),

    -- Update control
    update_enabled BOOLEAN DEFAULT TRUE,
    version_lock VARCHAR(64), -- Lock to specific version
    maintenance_mode BOOLEAN DEFAULT FALSE,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    labels JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Device update history
CREATE TABLE device_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(64) REFERENCES devices(device_id) ON DELETE CASCADE,

    -- Update details
    from_commit_hash VARCHAR(64),
    to_commit_hash VARCHAR(64) NOT NULL,
    update_status VARCHAR(32) NOT NULL, -- pending, in_progress, success, failed, rolled_back

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,

    -- Result
    error_message TEXT,
    rollback_reason TEXT,

    -- Health checks
    health_check_passed BOOLEAN,
    health_check_details JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Device heartbeats (high-frequency status updates)
CREATE TABLE device_heartbeats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(64) REFERENCES devices(device_id) ON DELETE CASCADE,

    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Quick status
    status VARCHAR(32) NOT NULL,
    commit_hash VARCHAR(64),
    uptime_seconds BIGINT,

    -- Resource metrics
    cpu_percent DECIMAL(5,2),
    memory_percent DECIMAL(5,2),
    disk_percent DECIMAL(5,2),
    temperature DECIMAL(5,2),

    -- Network
    ip_address INET,

    -- Container status
    containers_running INTEGER,
    containers_failed INTEGER,

    metadata JSONB DEFAULT '{}'
);

-- Create hypertable for time-series heartbeat data (if TimescaleDB is available)
-- SELECT create_hypertable('device_heartbeats', 'timestamp', if_not_exists => TRUE);

-- Device events and logs
CREATE TABLE device_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(64) REFERENCES devices(device_id) ON DELETE CASCADE,

    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_type VARCHAR(64) NOT NULL, -- registration, update, health_check, error, warning, info
    severity VARCHAR(16) DEFAULT 'info', -- critical, error, warning, info, debug

    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',

    -- Context
    commit_hash VARCHAR(64),
    component VARCHAR(64), -- agent, role, docker, system

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Deployment configurations
CREATE TABLE deployment_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(128) NOT NULL UNIQUE,

    -- Target specification
    branch VARCHAR(64) NOT NULL,
    segment VARCHAR(32), -- null = all segments
    role_filter VARCHAR(64), -- null = all roles
    device_filter JSONB, -- Advanced filtering

    -- Rollout strategy
    strategy VARCHAR(32) DEFAULT 'gradual', -- immediate, gradual, canary
    batch_size INTEGER DEFAULT 5,
    batch_delay_seconds INTEGER DEFAULT 300,
    max_failures INTEGER DEFAULT 2,

    -- Timing
    enabled BOOLEAN DEFAULT TRUE,
    schedule VARCHAR(128), -- Cron expression for scheduled updates

    -- Safety
    require_health_check BOOLEAN DEFAULT TRUE,
    auto_rollback BOOLEAN DEFAULT TRUE,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Deployment rollouts (tracking in-progress deployments)
CREATE TABLE deployment_rollouts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    deployment_config_id UUID REFERENCES deployment_configs(id),

    commit_hash VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'pending', -- pending, in_progress, completed, failed, cancelled

    -- Progress
    total_devices INTEGER DEFAULT 0,
    updated_devices INTEGER DEFAULT 0,
    failed_devices INTEGER DEFAULT 0,
    pending_devices INTEGER DEFAULT 0,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Control
    auto_halt_triggered BOOLEAN DEFAULT FALSE,
    halt_reason TEXT,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alert rules configuration
CREATE TABLE alert_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(128) NOT NULL UNIQUE,

    -- Rule definition
    rule_type VARCHAR(64) NOT NULL, -- device_offline, high_failure_rate, deployment_failed, etc.
    condition JSONB NOT NULL,

    -- Targeting
    device_filter JSONB,
    severity VARCHAR(16) DEFAULT 'warning',

    -- Actions
    enabled BOOLEAN DEFAULT TRUE,
    notification_channels JSONB DEFAULT '[]', -- email, slack, webhook, etc.

    -- Throttling
    cooldown_seconds INTEGER DEFAULT 300,
    last_triggered_at TIMESTAMP WITH TIME ZONE,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Alert history
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_rule_id UUID REFERENCES alert_rules(id),

    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    severity VARCHAR(16) NOT NULL,

    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,

    -- Context
    device_id VARCHAR(64) REFERENCES devices(device_id) ON DELETE SET NULL,
    deployment_rollout_id UUID REFERENCES deployment_rollouts(id) ON DELETE SET NULL,

    -- Status
    status VARCHAR(32) DEFAULT 'firing', -- firing, acknowledged, resolved
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(128),
    resolved_at TIMESTAMP WITH TIME ZONE,

    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API keys for device authentication
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key_hash VARCHAR(128) NOT NULL UNIQUE,

    device_id VARCHAR(64) REFERENCES devices(device_id) ON DELETE CASCADE,
    name VARCHAR(128),

    -- Permissions
    scopes JSONB DEFAULT '["read:status", "write:heartbeat"]',

    -- Validity
    enabled BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_role ON devices(role);
CREATE INDEX idx_devices_segment ON devices(segment);
CREATE INDEX idx_devices_last_seen ON devices(last_seen);
CREATE INDEX idx_devices_labels ON devices USING GIN(labels);

CREATE INDEX idx_device_updates_device_id ON device_updates(device_id);
CREATE INDEX idx_device_updates_status ON device_updates(update_status);
CREATE INDEX idx_device_updates_started_at ON device_updates(started_at);

CREATE INDEX idx_device_heartbeats_device_id ON device_heartbeats(device_id);
CREATE INDEX idx_device_heartbeats_timestamp ON device_heartbeats(timestamp DESC);

CREATE INDEX idx_device_events_device_id ON device_events(device_id);
CREATE INDEX idx_device_events_timestamp ON device_events(timestamp DESC);
CREATE INDEX idx_device_events_event_type ON device_events(event_type);
CREATE INDEX idx_device_events_severity ON device_events(severity);

CREATE INDEX idx_deployment_rollouts_status ON deployment_rollouts(status);
CREATE INDEX idx_deployment_rollouts_started_at ON deployment_rollouts(started_at DESC);

CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);
CREATE INDEX idx_alerts_device_id ON alerts(device_id);

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_devices_updated_at BEFORE UPDATE ON devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_deployment_configs_updated_at BEFORE UPDATE ON deployment_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alert_rules_updated_at BEFORE UPDATE ON alert_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE VIEW device_status_summary AS
SELECT
    status,
    COUNT(*) as device_count,
    COUNT(*) FILTER (WHERE last_seen > NOW() - INTERVAL '5 minutes') as online_count
FROM devices
GROUP BY status;

CREATE VIEW recent_failures AS
SELECT
    d.device_id,
    d.hostname,
    d.role,
    du.to_commit_hash,
    du.error_message,
    du.started_at
FROM device_updates du
JOIN devices d ON d.device_id = du.device_id
WHERE du.update_status = 'failed'
  AND du.started_at > NOW() - INTERVAL '24 hours'
ORDER BY du.started_at DESC;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fleet;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fleet;
GRANT USAGE ON SCHEMA public TO fleet;
