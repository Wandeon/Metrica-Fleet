/**
 * Metrica Fleet Dashboard - API Client
 *
 * Centralized API client for communicating with the Fleet Management API
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import type { ApiError } from '../types';

// Get API configuration from environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL || window.REACT_APP_API_URL || 'http://localhost:8080';
const API_KEY = import.meta.env.VITE_API_KEY || '';

/**
 * API Client Instance
 */
class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add API key to all requests if available
    if (API_KEY) {
      this.client.defaults.headers.common['X-API-Key'] = API_KEY;
    }

    // Request interceptor for logging and authentication
    this.client.interceptors.request.use(
      (config) => {
        // Add timestamp to avoid caching issues
        config.params = {
          ...config.params,
          _t: Date.now(),
        };
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const apiError = this.handleError(error);
        return Promise.reject(apiError);
      }
    );
  }

  /**
   * Handle API errors and convert to standard format
   */
  private handleError(error: AxiosError): ApiError {
    if (error.response) {
      // Server responded with error status
      const data = error.response.data as any;
      return {
        error: data?.error || 'API Error',
        message: data?.message || error.message,
        details: data?.details,
        status: error.response.status,
      };
    } else if (error.request) {
      // Request was made but no response received
      return {
        error: 'Network Error',
        message: 'Unable to reach the server. Please check your connection.',
        status: 0,
      };
    } else {
      // Something else happened
      return {
        error: 'Request Error',
        message: error.message,
        status: 0,
      };
    }
  }

  /**
   * GET request
   */
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  /**
   * POST request
   */
  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  /**
   * PUT request
   */
  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  /**
   * PATCH request
   */
  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  /**
   * DELETE request
   */
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  /**
   * Set API key for authentication
   */
  setApiKey(apiKey: string): void {
    this.client.defaults.headers.common['X-API-Key'] = apiKey;
  }

  /**
   * Remove API key
   */
  clearApiKey(): void {
    delete this.client.defaults.headers.common['X-API-Key'];
  }

  /**
   * Get base URL
   */
  getBaseUrl(): string {
    return API_BASE_URL;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export for testing
export default ApiClient;
