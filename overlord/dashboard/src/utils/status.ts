/**
 * Metrica Fleet Dashboard - Status Utilities
 */

import type { DeviceStatus, AlertSeverity, DeploymentStatus } from '../types';

/**
 * Get color class for device status
 */
export function getStatusColor(status: DeviceStatus): string {
  const colors: Record<DeviceStatus, string> = {
    healthy: 'text-success-600 bg-success-50',
    degraded: 'text-warning-600 bg-warning-50',
    offline: 'text-gray-600 bg-gray-50',
    error: 'text-danger-600 bg-danger-50',
    unknown: 'text-gray-600 bg-gray-50',
  };
  return colors[status] || colors.unknown;
}

/**
 * Get badge color for device status
 */
export function getStatusBadgeColor(status: DeviceStatus): string {
  const colors: Record<DeviceStatus, string> = {
    healthy: 'bg-success-100 text-success-800 border-success-300',
    degraded: 'bg-warning-100 text-warning-800 border-warning-300',
    offline: 'bg-gray-100 text-gray-800 border-gray-300',
    error: 'bg-danger-100 text-danger-800 border-danger-300',
    unknown: 'bg-gray-100 text-gray-800 border-gray-300',
  };
  return colors[status] || colors.unknown;
}

/**
 * Get color class for alert severity
 */
export function getAlertSeverityColor(severity: AlertSeverity): string {
  const colors: Record<AlertSeverity, string> = {
    critical: 'text-danger-600 bg-danger-50',
    warning: 'text-warning-600 bg-warning-50',
    info: 'text-primary-600 bg-primary-50',
  };
  return colors[severity];
}

/**
 * Get badge color for alert severity
 */
export function getAlertSeverityBadgeColor(severity: AlertSeverity): string {
  const colors: Record<AlertSeverity, string> = {
    critical: 'bg-danger-100 text-danger-800 border-danger-300',
    warning: 'bg-warning-100 text-warning-800 border-warning-300',
    info: 'bg-primary-100 text-primary-800 border-primary-300',
  };
  return colors[severity];
}

/**
 * Get color class for deployment status
 */
export function getDeploymentStatusColor(status: DeploymentStatus): string {
  const colors: Record<DeploymentStatus, string> = {
    pending: 'text-gray-600 bg-gray-50',
    running: 'text-primary-600 bg-primary-50',
    completed: 'text-success-600 bg-success-50',
    failed: 'text-danger-600 bg-danger-50',
    cancelled: 'text-gray-600 bg-gray-50',
  };
  return colors[status];
}

/**
 * Get badge color for deployment status
 */
export function getDeploymentStatusBadgeColor(status: DeploymentStatus): string {
  const colors: Record<DeploymentStatus, string> = {
    pending: 'bg-gray-100 text-gray-800 border-gray-300',
    running: 'bg-primary-100 text-primary-800 border-primary-300',
    completed: 'bg-success-100 text-success-800 border-success-300',
    failed: 'bg-danger-100 text-danger-800 border-danger-300',
    cancelled: 'bg-gray-100 text-gray-800 border-gray-300',
  };
  return colors[status];
}

/**
 * Get health status based on metric percentage
 */
export function getHealthStatus(
  value: number,
  warningThreshold: number,
  criticalThreshold: number
): 'healthy' | 'warning' | 'critical' {
  if (value >= criticalThreshold) return 'critical';
  if (value >= warningThreshold) return 'warning';
  return 'healthy';
}

/**
 * Get color for metric value
 */
export function getMetricColor(
  value: number,
  warningThreshold: number,
  criticalThreshold: number
): string {
  const status = getHealthStatus(value, warningThreshold, criticalThreshold);
  const colors = {
    healthy: 'text-success-600',
    warning: 'text-warning-600',
    critical: 'text-danger-600',
  };
  return colors[status];
}

/**
 * Get status icon name
 */
export function getStatusIcon(status: DeviceStatus): string {
  const icons: Record<DeviceStatus, string> = {
    healthy: 'check-circle',
    degraded: 'alert-triangle',
    offline: 'x-circle',
    error: 'alert-octagon',
    unknown: 'help-circle',
  };
  return icons[status] || icons.unknown;
}
