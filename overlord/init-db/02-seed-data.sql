-- Seed data for Metrica Fleet Overlord
-- Initial configurations and example data

-- Insert default deployment configurations
INSERT INTO deployment_configs (name, branch, segment, strategy, batch_size, batch_delay_seconds, max_failures, require_health_check, auto_rollback)
VALUES
    ('production-gradual', 'main', 'stable', 'gradual', 5, 300, 2, true, true),
    ('staging-immediate', 'staging', 'beta', 'immediate', 100, 0, 5, true, false),
    ('canary-deployment', 'main', 'canary', 'canary', 1, 600, 0, true, true);

-- Insert default alert rules
INSERT INTO alert_rules (name, rule_type, condition, severity, notification_channels, cooldown_seconds)
VALUES
    (
        'device-offline',
        'device_offline',
        '{"threshold_minutes": 5}',
        'critical',
        '["email", "slack"]',
        900
    ),
    (
        'high-failure-rate',
        'deployment_failure_rate',
        '{"threshold_percent": 20, "window_minutes": 30}',
        'error',
        '["email", "slack"]',
        600
    ),
    (
        'device-high-temperature',
        'temperature_threshold',
        '{"threshold_celsius": 80}',
        'warning',
        '["email"]',
        1800
    ),
    (
        'device-disk-full',
        'disk_usage',
        '{"threshold_percent": 90}',
        'warning',
        '["email", "slack"]',
        3600
    ),
    (
        'update-stuck',
        'update_timeout',
        '{"threshold_minutes": 30}',
        'error',
        '["email", "slack"]',
        1800
    );

-- Insert example test devices (optional - remove in production)
-- Uncomment these for testing
/*
INSERT INTO devices (device_id, hostname, role, branch, segment, status, ip_address)
VALUES
    ('pi-test-001', 'test-pi-001', 'camera-single', 'staging', 'canary', 'unknown', '192.168.1.101'),
    ('pi-test-002', 'test-pi-002', 'camera-dual', 'staging', 'beta', 'unknown', '192.168.1.102'),
    ('pi-test-003', 'test-pi-003', 'audio-player', 'main', 'stable', 'unknown', '192.168.1.103');
*/
