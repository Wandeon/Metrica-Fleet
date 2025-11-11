/**
 * Device Detail Page - Detailed view of a single device
 */

import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Activity, Cpu, HardDrive, Thermometer, Clock, GitBranch, Tag } from 'lucide-react';
import { useDevice } from '../hooks/useApi';
import Loading from '../components/common/Loading';
import ErrorMessage from '../components/common/ErrorMessage';
import StatusBadge from '../components/common/StatusBadge';
import { Card, CardHeader, CardBody } from '../components/common/Card';
import { formatRelativeTime, formatPercent, formatUptime, formatTemperature } from '../utils/format';

export default function DeviceDetail() {
  const { deviceId } = useParams<{ deviceId: string }>();
  const navigate = useNavigate();
  const { data: device, isLoading, error, refetch } = useDevice(deviceId!);

  if (isLoading) {
    return <Loading text="Loading device..." />;
  }

  if (error || !device) {
    return (
      <ErrorMessage
        message={(error as any)?.message || 'Device not found'}
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <button onClick={() => navigate('/devices')} className="btn btn-ghost mb-4 flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" />
          Back to Devices
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{device.hostname}</h1>
            <p className="text-gray-600">{device.device_id}</p>
          </div>
          <StatusBadge status={device.status} withDot />
        </div>
      </div>

      {/* Device Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Device Information
            </h2>
          </CardHeader>
          <CardBody className="space-y-3">
            <div>
              <p className="text-sm text-gray-600">Role</p>
              <p className="font-medium capitalize">{device.role}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">IP Address</p>
              <p className="font-medium">{device.ip_address}</p>
            </div>
            {device.tailscale_ip && (
              <div>
                <p className="text-sm text-gray-600">Tailscale IP</p>
                <p className="font-medium">{device.tailscale_ip}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-gray-600">Last Seen</p>
              <p className="font-medium">{formatRelativeTime(device.last_seen)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Registered</p>
              <p className="font-medium">{formatRelativeTime(device.registered_at)}</p>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <GitBranch className="w-5 h-5" />
              Deployment Configuration
            </h2>
          </CardHeader>
          <CardBody className="space-y-3">
            <div>
              <p className="text-sm text-gray-600">Branch</p>
              <p className="font-medium">{device.branch}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Segment</p>
              <p className="font-medium capitalize">{device.segment}</p>
            </div>
            {device.commit_hash && (
              <div>
                <p className="text-sm text-gray-600">Commit Hash</p>
                <p className="font-mono text-sm">{device.commit_hash.substring(0, 7)}</p>
              </div>
            )}
            {device.version && (
              <div>
                <p className="text-sm text-gray-600">Version</p>
                <p className="font-medium">{device.version}</p>
              </div>
            )}
            {device.agent_version && (
              <div>
                <p className="text-sm text-gray-600">Agent Version</p>
                <p className="font-medium">{device.agent_version}</p>
              </div>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Runtime Information
            </h2>
          </CardHeader>
          <CardBody className="space-y-3">
            {device.uptime_seconds !== undefined && (
              <div>
                <p className="text-sm text-gray-600">Uptime</p>
                <p className="font-medium">{formatUptime(device.uptime_seconds)}</p>
              </div>
            )}
            {device.temperature !== undefined && (
              <div>
                <p className="text-sm text-gray-600">Temperature</p>
                <p className="font-medium">{formatTemperature(device.temperature)}</p>
              </div>
            )}
            {device.tags && device.tags.length > 0 && (
              <div>
                <p className="text-sm text-gray-600 mb-2">Tags</p>
                <div className="flex flex-wrap gap-1">
                  {device.tags.map((tag) => (
                    <span key={tag} className="badge bg-gray-100 text-gray-800 border-gray-300">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">CPU Usage</p>
                <p className="text-3xl font-bold">{formatPercent(device.cpu_percent || 0)}</p>
              </div>
              <div className="p-3 rounded-lg bg-primary-50 text-primary-600">
                <Cpu className="w-8 h-8" />
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Memory Usage</p>
                <p className="text-3xl font-bold">{formatPercent(device.memory_percent || 0)}</p>
              </div>
              <div className="p-3 rounded-lg bg-success-50 text-success-600">
                <Activity className="w-8 h-8" />
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Disk Usage</p>
                <p className="text-3xl font-bold">{formatPercent(device.disk_percent || 0)}</p>
              </div>
              <div className="p-3 rounded-lg bg-warning-50 text-warning-600">
                <HardDrive className="w-8 h-8" />
              </div>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Actions */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Actions</h2>
        </CardHeader>
        <CardBody>
          <div className="flex flex-wrap gap-3">
            <button className="btn btn-secondary">View Logs</button>
            <button className="btn btn-secondary">View Metrics History</button>
            <button className="btn btn-secondary">Reboot Device</button>
            <button className="btn btn-danger">Remove from Fleet</button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
