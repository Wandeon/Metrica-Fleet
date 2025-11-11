/**
 * Deployments Page - Manage deployments
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Rocket, Plus } from 'lucide-react';
import { useDeployments, useCreateDeployment } from '../hooks/useApi';
import Loading from '../components/common/Loading';
import ErrorMessage from '../components/common/ErrorMessage';
import StatusBadge from '../components/common/StatusBadge';
import EmptyState from '../components/common/EmptyState';
import Modal from '../components/common/Modal';
import { Card, CardBody } from '../components/common/Card';
import { formatRelativeTime, formatPercent } from '../utils/format';
import type { DeploymentStrategy, DeploymentSegment, DeviceRole } from '../types';

export default function Deployments() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const { data, isLoading, error, refetch } = useDeployments();

  const createMutation = useCreateDeployment({
    onSuccess: () => {
      setIsCreateModalOpen(false);
      refetch();
    },
  });

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const segments = formData.getAll('segments') as DeploymentSegment[];

    createMutation.mutate({
      title: formData.get('title') as string,
      description: formData.get('description') as string,
      strategy: formData.get('strategy') as DeploymentStrategy,
      target_branch: formData.get('target_branch') as string,
      target_commit: formData.get('target_commit') as string,
      target_segments: segments,
    });
  };

  if (isLoading) {
    return <Loading text="Loading deployments..." />;
  }

  if (error) {
    return <ErrorMessage message={(error as any)?.message || 'Failed to load deployments'} onRetry={() => refetch()} />;
  }

  const deployments = data?.items || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Deployments</h1>
          <p className="text-gray-600">{data?.total || 0} total deployments</p>
        </div>
        <button onClick={() => setIsCreateModalOpen(true)} className="btn btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Deployment
        </button>
      </div>

      {/* Deployment List */}
      {deployments.length === 0 ? (
        <EmptyState
          icon={Rocket}
          title="No deployments yet"
          description="Create your first deployment to update devices in your fleet."
          action={{
            label: 'Create Deployment',
            onClick: () => setIsCreateModalOpen(true),
          }}
        />
      ) : (
        <div className="space-y-4">
          {deployments.map((deployment) => {
            const progress = deployment.total_devices > 0
              ? (deployment.completed_devices / deployment.total_devices) * 100
              : 0;

            return (
              <Link
                key={deployment.deployment_id}
                to={`/deployments/${deployment.deployment_id}`}
                className="card hover:shadow-md transition-shadow block"
              >
                <div className="card-body">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{deployment.title}</h3>
                      <p className="text-sm text-gray-600">{deployment.description}</p>
                    </div>
                    <StatusBadge status={deployment.status} type="deployment" />
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-gray-600">Strategy</p>
                      <p className="text-sm font-medium capitalize">{deployment.strategy}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Branch</p>
                      <p className="text-sm font-medium">{deployment.target_branch}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Progress</p>
                      <p className="text-sm font-medium">
                        {deployment.completed_devices}/{deployment.total_devices}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Created</p>
                      <p className="text-sm font-medium">{formatRelativeTime(deployment.created_at)}</p>
                    </div>
                  </div>

                  {deployment.status === 'running' && (
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {/* Create Deployment Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Deployment"
        size="lg"
        footer={
          <div className="flex justify-end gap-3">
            <button onClick={() => setIsCreateModalOpen(false)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" form="create-form" className="btn btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create Deployment'}
            </button>
          </div>
        }
      >
        <form id="create-form" onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="label">Title</label>
            <input name="title" type="text" required className="input" placeholder="Production Release v2.1.0" />
          </div>
          <div>
            <label className="label">Description</label>
            <textarea
              name="description"
              className="input"
              rows={3}
              placeholder="Describe what's included in this deployment..."
            />
          </div>
          <div>
            <label className="label">Deployment Strategy</label>
            <select name="strategy" required className="select">
              <option value="canary">Canary - Test on small group first</option>
              <option value="rolling">Rolling - Gradual rollout</option>
              <option value="immediate">Immediate - All at once</option>
              <option value="blue-green">Blue-Green - Zero downtime</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Target Branch</label>
              <input name="target_branch" type="text" required className="input" placeholder="main" defaultValue="main" />
            </div>
            <div>
              <label className="label">Target Commit</label>
              <input name="target_commit" type="text" required className="input" placeholder="abc123..." />
            </div>
          </div>
          <div>
            <label className="label">Target Segments</label>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input type="checkbox" name="segments" value="canary" className="rounded" />
                <span>Canary</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" name="segments" value="beta" className="rounded" />
                <span>Beta</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" name="segments" value="stable" className="rounded" defaultChecked />
                <span>Stable</span>
              </label>
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
}
