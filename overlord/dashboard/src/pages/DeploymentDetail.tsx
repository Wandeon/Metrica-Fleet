/**
 * Deployment Detail Page - Detailed view of a deployment
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock, CheckCircle, XCircle, Loader } from 'lucide-react';
import { useDeployment, useDeploymentProgress } from '../hooks/useApi';
import Loading from '../components/common/Loading';
import ErrorMessage from '../components/common/ErrorMessage';
import StatusBadge from '../components/common/StatusBadge';
import { Card, CardHeader, CardBody } from '../components/common/Card';
import { formatRelativeTime, formatDuration } from '../utils/format';

export default function DeploymentDetail() {
  const { deploymentId } = useParams<{ deploymentId: string }>();
  const navigate = useNavigate();
  const { data: deployment, isLoading, error } = useDeployment(deploymentId!);
  const { data: progress } = useDeploymentProgress(deploymentId!);

  if (isLoading) {
    return <Loading text="Loading deployment..." />;
  }

  if (error || !deployment) {
    return <ErrorMessage message={(error as any)?.message || 'Deployment not found'} />;
  }

  const progressPercent = deployment.total_devices > 0
    ? (deployment.completed_devices / deployment.total_devices) * 100
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <button onClick={() => navigate('/deployments')} className="btn btn-ghost mb-4 flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" />
          Back to Deployments
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{deployment.title}</h1>
            <p className="text-gray-600">{deployment.description}</p>
          </div>
          <StatusBadge status={deployment.status} type="deployment" />
        </div>
      </div>

      {/* Progress Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardBody>
            <p className="text-sm text-gray-600 mb-1">Total Devices</p>
            <p className="text-3xl font-bold">{deployment.total_devices}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-600 mb-1">Completed</p>
            <p className="text-3xl font-bold text-success-600">{deployment.completed_devices}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-600 mb-1">Failed</p>
            <p className="text-3xl font-bold text-danger-600">{deployment.failed_devices}</p>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <p className="text-sm text-gray-600 mb-1">Progress</p>
            <p className="text-3xl font-bold">{progressPercent.toFixed(0)}%</p>
          </CardBody>
        </Card>
      </div>

      {/* Progress Bar */}
      {deployment.status === 'running' && (
        <Card>
          <CardBody>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-primary-600 h-4 rounded-full transition-all flex items-center justify-end pr-2"
                style={{ width: `${progressPercent}%` }}
              >
                {progressPercent > 10 && (
                  <span className="text-xs font-medium text-white">{progressPercent.toFixed(0)}%</span>
                )}
              </div>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Deployment Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Deployment Configuration</h2>
          </CardHeader>
          <CardBody className="space-y-3">
            <div>
              <p className="text-sm text-gray-600">Strategy</p>
              <p className="font-medium capitalize">{deployment.strategy}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Target Branch</p>
              <p className="font-medium">{deployment.target_branch}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Target Commit</p>
              <p className="font-mono text-sm">{deployment.target_commit.substring(0, 7)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Target Segments</p>
              <div className="flex flex-wrap gap-2 mt-1">
                {deployment.target_segments.map((segment) => (
                  <span key={segment} className="badge bg-primary-100 text-primary-800 border-primary-300">
                    {segment}
                  </span>
                ))}
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Timeline</h2>
          </CardHeader>
          <CardBody className="space-y-3">
            <div>
              <p className="text-sm text-gray-600">Created</p>
              <p className="font-medium">{formatRelativeTime(deployment.created_at)}</p>
            </div>
            {deployment.started_at && (
              <div>
                <p className="text-sm text-gray-600">Started</p>
                <p className="font-medium">{formatRelativeTime(deployment.started_at)}</p>
              </div>
            )}
            {deployment.completed_at && (
              <div>
                <p className="text-sm text-gray-600">Completed</p>
                <p className="font-medium">{formatRelativeTime(deployment.completed_at)}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-gray-600">Created By</p>
              <p className="font-medium">{deployment.created_by}</p>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Device Progress */}
      {progress && progress.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold">Device Progress</h2>
          </CardHeader>
          <CardBody>
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th>Device ID</th>
                    <th>Status</th>
                    <th>Progress</th>
                    <th>Message</th>
                    <th>Started</th>
                  </tr>
                </thead>
                <tbody>
                  {progress.map((item) => (
                    <tr key={item.device_id}>
                      <td className="font-mono text-sm">{item.device_id}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          {item.status === 'completed' && <CheckCircle className="w-4 h-4 text-success-600" />}
                          {item.status === 'failed' && <XCircle className="w-4 h-4 text-danger-600" />}
                          {!['completed', 'failed'].includes(item.status) && (
                            <Loader className="w-4 h-4 text-primary-600 animate-spin" />
                          )}
                          <span className="capitalize">{item.status}</span>
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-primary-600 h-2 rounded-full"
                              style={{ width: `${item.progress_percent}%` }}
                            />
                          </div>
                          <span className="text-sm">{item.progress_percent}%</span>
                        </div>
                      </td>
                      <td className="text-sm text-gray-600">{item.message || '-'}</td>
                      <td className="text-sm">{item.started_at ? formatRelativeTime(item.started_at) : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      )}

      {/* Actions */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Actions</h2>
        </CardHeader>
        <CardBody>
          <div className="flex flex-wrap gap-3">
            {deployment.status === 'running' && (
              <button className="btn btn-danger">Cancel Deployment</button>
            )}
            {deployment.status === 'failed' && (
              <>
                <button className="btn btn-primary">Retry Failed Devices</button>
                {deployment.rollback_enabled && (
                  <button className="btn btn-warning">Rollback</button>
                )}
              </>
            )}
            <button className="btn btn-secondary">View Logs</button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
