/**
 * Device List Page - List and manage all devices
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Server, Plus, Search, Filter } from 'lucide-react';
import { useDevices, useRegisterDevice } from '../hooks/useApi';
import Loading from '../components/common/Loading';
import ErrorMessage from '../components/common/ErrorMessage';
import StatusBadge from '../components/common/StatusBadge';
import EmptyState from '../components/common/EmptyState';
import Modal from '../components/common/Modal';
import { Card, CardBody } from '../components/common/Card';
import { formatRelativeTime, formatPercent } from '../utils/format';
import type { DeviceRole, DeploymentSegment } from '../types';

export default function DeviceList() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);

  const { data, isLoading, error, refetch } = useDevices({
    status: statusFilter || undefined,
    role: roleFilter || undefined,
  });

  const registerMutation = useRegisterDevice({
    onSuccess: () => {
      setIsRegisterModalOpen(false);
      refetch();
    },
  });

  const handleRegister = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    registerMutation.mutate({
      device_id: formData.get('device_id') as string,
      hostname: formData.get('hostname') as string,
      role: formData.get('role') as DeviceRole,
      branch: formData.get('branch') as string,
      segment: formData.get('segment') as DeploymentSegment,
      ip_address: formData.get('ip_address') as string,
    });
  };

  if (isLoading) {
    return <Loading text="Loading devices..." />;
  }

  if (error) {
    return <ErrorMessage message={(error as any)?.message || 'Failed to load devices'} onRetry={() => refetch()} />;
  }

  const devices = data?.items || [];
  const filteredDevices = devices.filter((device) =>
    device.hostname.toLowerCase().includes(searchQuery.toLowerCase()) ||
    device.device_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Devices</h1>
          <p className="text-gray-600">{data?.total || 0} devices in your fleet</p>
        </div>
        <button onClick={() => setIsRegisterModalOpen(true)} className="btn btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Register Device
        </button>
      </div>

      {/* Filters */}
      <Card>
        <CardBody>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search devices..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input pl-10 w-full"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="select w-full md:w-48"
            >
              <option value="">All Statuses</option>
              <option value="healthy">Healthy</option>
              <option value="degraded">Degraded</option>
              <option value="offline">Offline</option>
              <option value="error">Error</option>
            </select>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="select w-full md:w-48"
            >
              <option value="">All Roles</option>
              <option value="camera-single">Camera Single</option>
              <option value="camera-multi">Camera Multi</option>
              <option value="controller">Controller</option>
              <option value="gateway">Gateway</option>
              <option value="sensor">Sensor</option>
            </select>
          </div>
        </CardBody>
      </Card>

      {/* Device List */}
      {filteredDevices.length === 0 ? (
        <EmptyState
          icon={Server}
          title="No devices found"
          description="Get started by registering your first device to the fleet."
          action={{
            label: 'Register Device',
            onClick: () => setIsRegisterModalOpen(true),
          }}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredDevices.map((device) => (
            <Link
              key={device.device_id}
              to={`/devices/${device.device_id}`}
              className="card hover:shadow-md transition-shadow"
            >
              <div className="card-body">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{device.hostname}</h3>
                    <p className="text-sm text-gray-600">{device.device_id}</p>
                  </div>
                  <StatusBadge status={device.status} withDot />
                </div>

                <div className="grid grid-cols-2 gap-4 mb-3">
                  <div>
                    <p className="text-xs text-gray-600">Role</p>
                    <p className="text-sm font-medium capitalize">{device.role}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Branch</p>
                    <p className="text-sm font-medium">{device.branch}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Segment</p>
                    <p className="text-sm font-medium capitalize">{device.segment}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-600">Last Seen</p>
                    <p className="text-sm font-medium">{formatRelativeTime(device.last_seen)}</p>
                  </div>
                </div>

                {device.cpu_percent !== undefined && (
                  <div className="pt-3 border-t border-gray-200">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-600">CPU</span>
                      <span className="font-medium">{formatPercent(device.cpu_percent)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm mt-1">
                      <span className="text-gray-600">Memory</span>
                      <span className="font-medium">{formatPercent(device.memory_percent || 0)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm mt-1">
                      <span className="text-gray-600">Disk</span>
                      <span className="font-medium">{formatPercent(device.disk_percent || 0)}</span>
                    </div>
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Register Device Modal */}
      <Modal
        isOpen={isRegisterModalOpen}
        onClose={() => setIsRegisterModalOpen(false)}
        title="Register New Device"
        footer={
          <div className="flex justify-end gap-3">
            <button onClick={() => setIsRegisterModalOpen(false)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" form="register-form" className="btn btn-primary" disabled={registerMutation.isPending}>
              {registerMutation.isPending ? 'Registering...' : 'Register'}
            </button>
          </div>
        }
      >
        <form id="register-form" onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="label">Device ID</label>
            <input name="device_id" type="text" required className="input" placeholder="pi-camera-001" />
          </div>
          <div>
            <label className="label">Hostname</label>
            <input name="hostname" type="text" required className="input" placeholder="camera-01" />
          </div>
          <div>
            <label className="label">Role</label>
            <select name="role" required className="select">
              <option value="camera-single">Camera Single</option>
              <option value="camera-multi">Camera Multi</option>
              <option value="controller">Controller</option>
              <option value="gateway">Gateway</option>
              <option value="sensor">Sensor</option>
            </select>
          </div>
          <div>
            <label className="label">Branch</label>
            <input name="branch" type="text" required className="input" placeholder="main" defaultValue="main" />
          </div>
          <div>
            <label className="label">Segment</label>
            <select name="segment" required className="select">
              <option value="stable">Stable</option>
              <option value="beta">Beta</option>
              <option value="canary">Canary</option>
              <option value="development">Development</option>
            </select>
          </div>
          <div>
            <label className="label">IP Address</label>
            <input name="ip_address" type="text" required className="input" placeholder="192.168.1.100" />
          </div>
        </form>
      </Modal>
    </div>
  );
}
