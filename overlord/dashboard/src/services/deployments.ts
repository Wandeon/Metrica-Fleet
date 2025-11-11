/**
 * Metrica Fleet Dashboard - Deployment Service
 *
 * Service layer for deployment management operations
 */

import { apiClient } from './api';
import type {
  Deployment,
  DeploymentCreate,
  DeploymentProgress,
  DeploymentStatistics,
  PaginatedResponse,
} from '../types';

/**
 * Deployment Service
 */
export const deploymentService = {
  /**
   * Get all deployments
   */
  async getDeployments(params?: {
    status?: string;
    strategy?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Deployment>> {
    return apiClient.get<PaginatedResponse<Deployment>>('/deployments', { params });
  },

  /**
   * Get a specific deployment
   */
  async getDeployment(deploymentId: string): Promise<Deployment> {
    return apiClient.get<Deployment>(`/deployments/${deploymentId}`);
  },

  /**
   * Create a new deployment
   */
  async createDeployment(data: DeploymentCreate): Promise<Deployment> {
    return apiClient.post<Deployment>('/deployments', data);
  },

  /**
   * Cancel a running deployment
   */
  async cancelDeployment(deploymentId: string): Promise<void> {
    return apiClient.post(`/deployments/${deploymentId}/cancel`);
  },

  /**
   * Rollback a deployment
   */
  async rollbackDeployment(deploymentId: string): Promise<Deployment> {
    return apiClient.post<Deployment>(`/deployments/${deploymentId}/rollback`);
  },

  /**
   * Get deployment progress for all devices
   */
  async getDeploymentProgress(deploymentId: string): Promise<DeploymentProgress[]> {
    return apiClient.get<DeploymentProgress[]>(`/deployments/${deploymentId}/progress`);
  },

  /**
   * Get deployment statistics
   */
  async getStatistics(): Promise<DeploymentStatistics> {
    return apiClient.get<DeploymentStatistics>('/deployments/statistics');
  },

  /**
   * Retry failed deployment on specific devices
   */
  async retryDeployment(deploymentId: string, deviceIds: string[]): Promise<void> {
    return apiClient.post(`/deployments/${deploymentId}/retry`, { device_ids: deviceIds });
  },

  /**
   * Get deployment logs
   */
  async getDeploymentLogs(deploymentId: string): Promise<any> {
    return apiClient.get(`/deployments/${deploymentId}/logs`);
  },
};

export default deploymentService;
