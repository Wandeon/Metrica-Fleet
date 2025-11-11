/**
 * Alerts Page - View and manage alerts
 */

import React, { useState } from 'react';
import { Bell, AlertTriangle, Info, CheckCircle } from 'lucide-react';
import { useAlerts, useAcknowledgeAlert, useResolveAlert } from '../hooks/useApi';
import Loading from '../components/common/Loading';
import ErrorMessage from '../components/common/ErrorMessage';
import StatusBadge from '../components/common/StatusBadge';
import EmptyState from '../components/common/EmptyState';
import { Card, CardBody } from '../components/common/Card';
import { formatRelativeTime } from '../utils/format';
import type { AlertSeverity } from '../types';

export default function Alerts() {
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('firing');

  const { data, isLoading, error, refetch } = useAlerts({
    severity: severityFilter || undefined,
    status: statusFilter || undefined,
  });

  const acknowledgeMutation = useAcknowledgeAlert({
    onSuccess: () => refetch(),
  });

  const resolveMutation = useResolveAlert({
    onSuccess: () => refetch(),
  });

  if (isLoading) {
    return <Loading text="Loading alerts..." />;
  }

  if (error) {
    return <ErrorMessage message={(error as any)?.message || 'Failed to load alerts'} onRetry={() => refetch()} />;
  }

  const alerts = data?.items || [];

  const getSeverityIcon = (severity: AlertSeverity) => {
    switch (severity) {
      case 'critical':
        return AlertTriangle;
      case 'warning':
        return Bell;
      case 'info':
        return Info;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Alerts</h1>
        <p className="text-gray-600">{data?.total || 0} alerts</p>
      </div>

      {/* Filters */}
      <Card>
        <CardBody>
          <div className="flex flex-col md:flex-row gap-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="select w-full md:w-48"
            >
              <option value="">All Statuses</option>
              <option value="firing">Firing</option>
              <option value="resolved">Resolved</option>
              <option value="acknowledged">Acknowledged</option>
            </select>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="select w-full md:w-48"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>
        </CardBody>
      </Card>

      {/* Alert List */}
      {alerts.length === 0 ? (
        <EmptyState
          icon={CheckCircle}
          title="No alerts"
          description={
            statusFilter === 'firing'
              ? 'All systems are running smoothly!'
              : 'No alerts match your current filters.'
          }
        />
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => {
            const SeverityIcon = getSeverityIcon(alert.severity);

            return (
              <Card key={alert.alert_id} className="hover:shadow-md transition-shadow">
                <CardBody>
                  <div className="flex items-start gap-4">
                    <div
                      className={`p-3 rounded-lg ${
                        alert.severity === 'critical'
                          ? 'bg-danger-50 text-danger-600'
                          : alert.severity === 'warning'
                          ? 'bg-warning-50 text-warning-600'
                          : 'bg-primary-50 text-primary-600'
                      }`}
                    >
                      <SeverityIcon className="w-6 h-6" />
                    </div>

                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{alert.alert_name}</h3>
                          <p className="text-sm text-gray-600">{alert.message}</p>
                        </div>
                        <StatusBadge status={alert.severity} type="alert" />
                      </div>

                      {alert.description && (
                        <p className="text-sm text-gray-600 mb-3">{alert.description}</p>
                      )}

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                        <div>
                          <p className="text-xs text-gray-600">Device</p>
                          <p className="text-sm font-medium">{alert.device_id || 'Fleet-wide'}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600">Source</p>
                          <p className="text-sm font-medium">{alert.source}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600">Started</p>
                          <p className="text-sm font-medium">{formatRelativeTime(alert.starts_at)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-600">Status</p>
                          <p className="text-sm font-medium capitalize">{alert.status}</p>
                        </div>
                      </div>

                      {alert.status === 'firing' && (
                        <div className="flex flex-wrap gap-2 pt-3 border-t border-gray-200">
                          <button
                            onClick={() =>
                              acknowledgeMutation.mutate({
                                alertId: alert.alert_id,
                                acknowledgedBy: 'admin',
                              })
                            }
                            disabled={acknowledgeMutation.isPending}
                            className="btn btn-sm btn-secondary"
                          >
                            Acknowledge
                          </button>
                          <button
                            onClick={() => resolveMutation.mutate(alert.alert_id)}
                            disabled={resolveMutation.isPending}
                            className="btn btn-sm btn-success"
                          >
                            Resolve
                          </button>
                          {alert.runbook_url && (
                            <a
                              href={alert.runbook_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="btn btn-sm btn-ghost"
                            >
                              View Runbook
                            </a>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </CardBody>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
