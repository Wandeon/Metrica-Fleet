/**
 * Metrica Fleet Dashboard - Device Service
 *
 * Service layer for device management operations
 */

import { apiClient } from './api';
import type {
  Device,
  DeviceRegistration,
  DeviceHeartbeat,
  DeviceUpdate,
  DeviceStatistics,
  PaginatedResponse,
} from '../types';

/**
 * Device Service
 */
export const deviceService = {
  /**
   * Get all devices
   */
  async getDevices(params?: {
    role?: string;
    status?: string;
    branch?: string;
    segment?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Device>> {
    return apiClient.get<PaginatedResponse<Device>>('/devices', { params });
  },

  /**
   * Get a specific device by ID
   */
  async getDevice(deviceId: string): Promise<Device> {
    return apiClient.get<Device>(`/devices/${deviceId}`);
  },

  /**
   * Register a new device
   */
  async registerDevice(data: DeviceRegistration): Promise<Device> {
    return apiClient.post<Device>('/devices/register', data);
  },

  /**
   * Update device information
   */
  async updateDevice(deviceId: string, data: DeviceUpdate): Promise<Device> {
    return apiClient.patch<Device>(`/devices/${deviceId}`, data);
  },

  /**
   * Delete a device
   */
  async deleteDevice(deviceId: string): Promise<void> {
    return apiClient.delete(`/devices/${deviceId}`);
  },

  /**
   * Send device heartbeat
   */
  async sendHeartbeat(deviceId: string, data: DeviceHeartbeat): Promise<void> {
    return apiClient.post(`/devices/${deviceId}/heartbeat`, data);
  },

  /**
   * Get device statistics
   */
  async getStatistics(): Promise<DeviceStatistics> {
    return apiClient.get<DeviceStatistics>('/devices/statistics');
  },

  /**
   * Get device metrics history
   */
  async getDeviceMetrics(
    deviceId: string,
    params: {
      metric: 'cpu' | 'memory' | 'disk' | 'temperature';
      start_time: string;
      end_time: string;
      interval?: string;
    }
  ): Promise<any> {
    return apiClient.get(`/devices/${deviceId}/metrics`, { params });
  },

  /**
   * Reboot device
   */
  async rebootDevice(deviceId: string): Promise<void> {
    return apiClient.post(`/devices/${deviceId}/reboot`);
  },

  /**
   * Get device logs
   */
  async getDeviceLogs(
    deviceId: string,
    params: {
      start_time: string;
      end_time: string;
      level?: string;
      limit?: number;
    }
  ): Promise<any> {
    return apiClient.get(`/devices/${deviceId}/logs`, { params });
  },
};

export default deviceService;
