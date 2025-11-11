/**
 * Dashboard Page - Fleet overview and statistics
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Server, Activity, AlertTriangle, Rocket, TrendingUp, ArrowRight } from 'lucide-react';
import { useFleetMetrics, useDeviceStatistics, useDeployments, useAlerts } from '../hooks/useApi';
import Loading from '../components/common/Loading';
import ErrorMessage from '../components/common/ErrorMessage';
import StatCard from '../components/common/StatCard';
import StatusBadge from '../components/common/StatusBadge';
import { Card, CardHeader, CardBody } from '../components/common/Card';
import { formatPercent, formatRelativeTime } from '../utils/format';

export default function Dashboard() {
  const { data: fleetMetrics, isLoading: metricsLoading, error: metricsError, refetch: refetchMetrics } = useFleetMetrics();
  const { data: deviceStats, isLoading: statsLoading } = useDeviceStatistics();
  const { data: deploymentsData, isLoading: deploymentsLoading } = useDeployments({ page: 1, page_size: 5 });
  const { data: alertsData, isLoading: alertsLoading } = useAlerts({ status: 'firing', page: 1, page_size: 5 });

  if (metricsLoading || statsLoading) {
    return <Loading text="Loading dashboard..." />;
  }

  if (metricsError) {
    return (
      <ErrorMessage
        message={(metricsError as any)?.message || 'Failed to load dashboard data'}
        onRetry={() => refetchMetrics()}
      />
    );
  }

  const healthPercentage = fleetMetrics
    ? ((fleetMetrics.healthy_devices / fleetMetrics.total_devices) * 100).toFixed(0)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">Overview of your Raspberry Pi fleet</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Devices"
          value={fleetMetrics?.total_devices || 0}
          icon={Server}
          color="primary"
        />
        <StatCard
          title="Healthy Devices"
          value={`${fleetMetrics?.healthy_devices || 0} (${healthPercentage}%)`}
          icon={Activity}
          color="success"
        />
        <StatCard
          title="Active Alerts"
          value={fleetMetrics?.active_alerts || 0}
          icon={AlertTriangle}
          color="warning"
        />
        <StatCard
          title="Active Deployments"
          value={fleetMetrics?.active_deployments || 0}
          icon={Rocket}
          color="primary"
        />
      </div>

      {/* Fleet Health Overview */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Fleet Health</h2>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-success-600">{fleetMetrics?.healthy_devices || 0}</p>
              <p className="text-sm text-gray-600 mt-1">Healthy</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-warning-600">{fleetMetrics?.degraded_devices || 0}</p>
              <p className="text-sm text-gray-600 mt-1">Degraded</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-600">{fleetMetrics?.offline_devices || 0}</p>
              <p className="text-sm text-gray-600 mt-1">Offline</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-danger-600">{fleetMetrics?.error_devices || 0}</p>
              <p className="text-sm text-gray-600 mt-1">Error</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-600">{fleetMetrics?.total_devices || 0}</p>
              <p className="text-sm text-gray-600 mt-1">Total</p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t border-gray-200">
            <div>
              <p className="text-sm text-gray-600 mb-1">Average CPU Usage</p>
              <p className="text-xl font-bold">{formatPercent(fleetMetrics?.avg_cpu_percent || 0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Average Memory Usage</p>
              <p className="text-xl font-bold">{formatPercent(fleetMetrics?.avg_memory_percent || 0)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-1">Average Disk Usage</p>
              <p className="text-xl font-bold">{formatPercent(fleetMetrics?.avg_disk_percent || 0)}</p>
            </div>
          </div>
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Deployments */}
        <Card>
          <CardHeader className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent Deployments</h2>
            <Link to="/deployments" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
              View All <ArrowRight className="w-4 h-4" />
            </Link>
          </CardHeader>
          <CardBody>
            {deploymentsLoading ? (
              <Loading size="sm" />
            ) : deploymentsData && deploymentsData.items.length > 0 ? (
              <div className="space-y-3">
                {deploymentsData.items.map((deployment) => (
                  <Link
                    key={deployment.deployment_id}
                    to={`/deployments/${deployment.deployment_id}`}
                    className="block p-3 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50/50 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-gray-900">{deployment.title}</h3>
                      <StatusBadge status={deployment.status} type="deployment" />
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{deployment.description}</p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{deployment.strategy} deployment</span>
                      <span>{formatRelativeTime(deployment.created_at)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-gray-600 text-center py-4">No recent deployments</p>
            )}
          </CardBody>
        </Card>

        {/* Active Alerts */}
        <Card>
          <CardHeader className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Active Alerts</h2>
            <Link to="/alerts" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
              View All <ArrowRight className="w-4 h-4" />
            </Link>
          </CardHeader>
          <CardBody>
            {alertsLoading ? (
              <Loading size="sm" />
            ) : alertsData && alertsData.items.length > 0 ? (
              <div className="space-y-3">
                {alertsData.items.map((alert) => (
                  <div
                    key={alert.alert_id}
                    className="p-3 rounded-lg border border-gray-200 hover:border-primary-300 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-gray-900">{alert.alert_name}</h3>
                      <StatusBadge status={alert.severity} type="alert" />
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{alert.message}</p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{alert.device_id || 'Fleet-wide'}</span>
                      <span>{formatRelativeTime(alert.starts_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-success-600 text-center py-4">No active alerts - all systems healthy!</p>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Device Statistics by Role */}
      {deviceStats && (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Devices by Role</h2>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(deviceStats.by_role).map(([role, count]) => (
                <div key={role} className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900">{count}</p>
                  <p className="text-sm text-gray-600 mt-1 capitalize">{role}</p>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
