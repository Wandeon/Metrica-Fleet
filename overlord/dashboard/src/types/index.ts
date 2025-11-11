/**
 * Metrica Fleet Dashboard - Type Definitions
 *
 * Complete TypeScript type definitions for the Fleet Management system
 */

// ============================================================================
// Device Types
// ============================================================================

export type DeviceRole = 'camera-single' | 'camera-multi' | 'controller' | 'gateway' | 'sensor';
export type DeviceStatus = 'healthy' | 'degraded' | 'offline' | 'error' | 'unknown';
export type DeploymentSegment = 'stable' | 'beta' | 'canary' | 'development';

export interface Device {
  device_id: string;
  hostname: string;
  role: DeviceRole;
  status: DeviceStatus;
  branch: string;
  segment: DeploymentSegment;
  ip_address: string;
  tailscale_ip?: string;
  commit_hash?: string;
  last_seen: string;
  registered_at: string;
  updated_at: string;

  // Metrics
  uptime_seconds?: number;
  cpu_percent?: number;
  memory_percent?: number;
  disk_percent?: number;
  temperature?: number;

  // Metadata
  version?: string;
  agent_version?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface DeviceRegistration {
  device_id: string;
  hostname: string;
  role: DeviceRole;
  branch: string;
  segment: DeploymentSegment;
  ip_address: string;
  tailscale_ip?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

export interface DeviceHeartbeat {
  status: DeviceStatus;
  commit_hash: string;
  uptime_seconds: number;
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  temperature?: number;
  agent_version?: string;
  metadata?: Record<string, any>;
}

export interface DeviceUpdate {
  hostname?: string;
  role?: DeviceRole;
  branch?: string;
  segment?: DeploymentSegment;
  ip_address?: string;
  tailscale_ip?: string;
  tags?: string[];
  metadata?: Record<string, any>;
}

// ============================================================================
// Deployment Types
// ============================================================================

export type DeploymentStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type DeploymentStrategy = 'immediate' | 'canary' | 'rolling' | 'blue-green';

export interface Deployment {
  deployment_id: string;
  title: string;
  description?: string;
  strategy: DeploymentStrategy;
  status: DeploymentStatus;

  // Target configuration
  target_branch: string;
  target_commit: string;
  target_segments: DeploymentSegment[];
  target_roles?: DeviceRole[];
  target_devices?: string[];

  // Progress tracking
  total_devices: number;
  completed_devices: number;
  failed_devices: number;

  // Timing
  created_at: string;
  started_at?: string;
  completed_at?: string;

  // Metadata
  created_by: string;
  rollback_enabled: boolean;
  auto_rollback_on_failure: boolean;
  metadata?: Record<string, any>;
}

export interface DeploymentCreate {
  title: string;
  description?: string;
  strategy: DeploymentStrategy;
  target_branch: string;
  target_commit: string;
  target_segments: DeploymentSegment[];
  target_roles?: DeviceRole[];
  target_devices?: string[];
  rollback_enabled?: boolean;
  auto_rollback_on_failure?: boolean;
}

export interface DeploymentProgress {
  deployment_id: string;
  device_id: string;
  status: 'pending' | 'downloading' | 'installing' | 'verifying' | 'completed' | 'failed';
  progress_percent: number;
  message?: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

// ============================================================================
// Alert Types
// ============================================================================

export type AlertSeverity = 'critical' | 'warning' | 'info';
export type AlertStatus = 'firing' | 'resolved' | 'acknowledged';

export interface Alert {
  alert_id: string;
  alert_name: string;
  severity: AlertSeverity;
  status: AlertStatus;
  message: string;
  description?: string;

  // Source
  device_id?: string;
  source: string;

  // Labels and annotations
  labels: Record<string, string>;
  annotations: Record<string, string>;

  // Timing
  starts_at: string;
  ends_at?: string;
  acknowledged_at?: string;
  acknowledged_by?: string;

  // Actions
  silence_until?: string;
  runbook_url?: string;
}

export interface AlertRule {
  rule_id: string;
  name: string;
  description: string;
  severity: AlertSeverity;
  enabled: boolean;

  // Conditions
  query: string;
  duration: string;
  threshold?: number;

  // Notification
  notify_channels: string[];

  // Metadata
  created_at: string;
  updated_at: string;
  created_by: string;
}

// ============================================================================
// Metrics Types
// ============================================================================

export interface MetricDataPoint {
  timestamp: string;
  value: number;
}

export interface DeviceMetrics {
  device_id: string;
  cpu_percent: MetricDataPoint[];
  memory_percent: MetricDataPoint[];
  disk_percent: MetricDataPoint[];
  temperature?: MetricDataPoint[];
  network_rx_bytes?: MetricDataPoint[];
  network_tx_bytes?: MetricDataPoint[];
}

export interface FleetMetrics {
  total_devices: number;
  healthy_devices: number;
  degraded_devices: number;
  offline_devices: number;
  error_devices: number;

  avg_cpu_percent: number;
  avg_memory_percent: number;
  avg_disk_percent: number;
  avg_temperature?: number;

  active_deployments: number;
  active_alerts: number;

  timestamp: string;
}

// ============================================================================
// Log Types
// ============================================================================

export type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  device_id?: string;
  source: string;
  message: string;
  context?: Record<string, any>;
}

export interface LogQuery {
  device_id?: string;
  level?: LogLevel;
  source?: string;
  search?: string;
  start_time: string;
  end_time: string;
  limit?: number;
}

// ============================================================================
// Configuration Types
// ============================================================================

export interface FleetConfig {
  deployment: {
    default_strategy: DeploymentStrategy;
    canary_percentage: number;
    rolling_batch_size: number;
    health_check_timeout: number;
    rollback_on_failure: boolean;
  };

  monitoring: {
    heartbeat_interval: number;
    metrics_retention_days: number;
    alert_evaluation_interval: number;
  };

  health: {
    cpu_warning_threshold: number;
    cpu_critical_threshold: number;
    memory_warning_threshold: number;
    memory_critical_threshold: number;
    disk_warning_threshold: number;
    disk_critical_threshold: number;
    temperature_warning_threshold?: number;
    temperature_critical_threshold?: number;
  };
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, any>;
  status: number;
}

// ============================================================================
// Statistics Types
// ============================================================================

export interface DeviceStatistics {
  by_role: Record<DeviceRole, number>;
  by_status: Record<DeviceStatus, number>;
  by_segment: Record<DeploymentSegment, number>;
  by_branch: Record<string, number>;
  total: number;
}

export interface DeploymentStatistics {
  total_deployments: number;
  successful_deployments: number;
  failed_deployments: number;
  running_deployments: number;
  average_duration_seconds: number;
  success_rate: number;
}

// ============================================================================
// User/Auth Types (for future implementation)
// ============================================================================

export interface User {
  user_id: string;
  username: string;
  email: string;
  role: 'admin' | 'operator' | 'viewer';
  created_at: string;
  last_login?: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// ============================================================================
// UI State Types
// ============================================================================

export interface TableFilter {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'contains' | 'in';
  value: any;
}

export interface TableSort {
  field: string;
  direction: 'asc' | 'desc';
}

export interface TableState {
  filters: TableFilter[];
  sort?: TableSort;
  page: number;
  pageSize: number;
}

export interface DashboardLayout {
  widgets: DashboardWidget[];
}

export interface DashboardWidget {
  id: string;
  type: 'chart' | 'stat' | 'table' | 'alert-list' | 'device-list';
  title: string;
  position: { x: number; y: number; w: number; h: number };
  config: Record<string, any>;
}
