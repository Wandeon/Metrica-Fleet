/**
 * Metrica Fleet Dashboard - Metrics Service
 *
 * Service layer for metrics and monitoring data
 */

import { apiClient } from './api';
import type { FleetMetrics, DeviceMetrics } from '../types';

/**
 * Metrics Service
 */
export const metricsService = {
  /**
   * Get current fleet-wide metrics
   */
  async getFleetMetrics(): Promise<FleetMetrics> {
    return apiClient.get<FleetMetrics>('/metrics/fleet');
  },

  /**
   * Get fleet metrics history
   */
  async getFleetMetricsHistory(params: {
    start_time: string;
    end_time: string;
    interval?: string;
  }): Promise<FleetMetrics[]> {
    return apiClient.get<FleetMetrics[]>('/metrics/fleet/history', { params });
  },

  /**
   * Get device metrics
   */
  async getDeviceMetrics(
    deviceId: string,
    params: {
      start_time: string;
      end_time: string;
      metrics?: string[];
      interval?: string;
    }
  ): Promise<DeviceMetrics> {
    return apiClient.get<DeviceMetrics>(`/metrics/devices/${deviceId}`, { params });
  },

  /**
   * Get aggregated metrics for multiple devices
   */
  async getAggregatedMetrics(params: {
    device_ids?: string[];
    role?: string;
    segment?: string;
    metric: string;
    aggregation: 'avg' | 'min' | 'max' | 'sum' | 'count';
    start_time: string;
    end_time: string;
    interval?: string;
  }): Promise<any> {
    return apiClient.get('/metrics/aggregate', { params });
  },

  /**
   * Query Prometheus directly
   */
  async queryPrometheus(query: string, time?: string): Promise<any> {
    return apiClient.post('/metrics/query', { query, time });
  },

  /**
   * Query Prometheus range
   */
  async queryPrometheusRange(query: string, start: string, end: string, step: string): Promise<any> {
    return apiClient.post('/metrics/query_range', {
      query,
      start,
      end,
      step,
    });
  },
};

export default metricsService;
