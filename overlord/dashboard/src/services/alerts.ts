/**
 * Metrica Fleet Dashboard - Alert Service
 *
 * Service layer for alert management operations
 */

import { apiClient } from './api';
import type { Alert, AlertRule, PaginatedResponse } from '../types';

/**
 * Alert Service
 */
export const alertService = {
  /**
   * Get all alerts
   */
  async getAlerts(params?: {
    status?: string;
    severity?: string;
    device_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Alert>> {
    return apiClient.get<PaginatedResponse<Alert>>('/alerts', { params });
  },

  /**
   * Get a specific alert
   */
  async getAlert(alertId: string): Promise<Alert> {
    return apiClient.get<Alert>(`/alerts/${alertId}`);
  },

  /**
   * Acknowledge an alert
   */
  async acknowledgeAlert(alertId: string, acknowledgedBy: string): Promise<Alert> {
    return apiClient.post<Alert>(`/alerts/${alertId}/acknowledge`, { acknowledged_by: acknowledgedBy });
  },

  /**
   * Resolve an alert
   */
  async resolveAlert(alertId: string): Promise<Alert> {
    return apiClient.post<Alert>(`/alerts/${alertId}/resolve`);
  },

  /**
   * Silence an alert
   */
  async silenceAlert(alertId: string, silenceUntil: string): Promise<Alert> {
    return apiClient.post<Alert>(`/alerts/${alertId}/silence`, { silence_until: silenceUntil });
  },

  /**
   * Get all alert rules
   */
  async getAlertRules(): Promise<AlertRule[]> {
    return apiClient.get<AlertRule[]>('/alerts/rules');
  },

  /**
   * Create a new alert rule
   */
  async createAlertRule(rule: Omit<AlertRule, 'rule_id' | 'created_at' | 'updated_at'>): Promise<AlertRule> {
    return apiClient.post<AlertRule>('/alerts/rules', rule);
  },

  /**
   * Update an alert rule
   */
  async updateAlertRule(ruleId: string, updates: Partial<AlertRule>): Promise<AlertRule> {
    return apiClient.patch<AlertRule>(`/alerts/rules/${ruleId}`, updates);
  },

  /**
   * Delete an alert rule
   */
  async deleteAlertRule(ruleId: string): Promise<void> {
    return apiClient.delete(`/alerts/rules/${ruleId}`);
  },

  /**
   * Enable/disable an alert rule
   */
  async toggleAlertRule(ruleId: string, enabled: boolean): Promise<AlertRule> {
    return apiClient.patch<AlertRule>(`/alerts/rules/${ruleId}`, { enabled });
  },
};

export default alertService;
