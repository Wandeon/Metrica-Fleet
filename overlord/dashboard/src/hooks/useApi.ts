/**
 * Metrica Fleet Dashboard - API Hooks
 *
 * React Query hooks for API operations
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { deviceService, deploymentService, alertService, metricsService } from '../services';
import type { Device, Deployment, Alert, FleetMetrics } from '../types';

// ============================================================================
// Device Hooks
// ============================================================================

export function useDevices(params?: any, options?: UseQueryOptions<any>) {
  return useQuery({
    queryKey: ['devices', params],
    queryFn: () => deviceService.getDevices(params),
    ...options,
  });
}

export function useDevice(deviceId: string, options?: UseQueryOptions<Device>) {
  return useQuery({
    queryKey: ['devices', deviceId],
    queryFn: () => deviceService.getDevice(deviceId),
    enabled: !!deviceId,
    ...options,
  });
}

export function useDeviceStatistics(options?: UseQueryOptions<any>) {
  return useQuery({
    queryKey: ['devices', 'statistics'],
    queryFn: () => deviceService.getStatistics(),
    ...options,
  });
}

export function useRegisterDevice(options?: UseMutationOptions<Device, any, any>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data) => deviceService.registerDevice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
    ...options,
  });
}

export function useUpdateDevice(options?: UseMutationOptions<Device, any, { deviceId: string; data: any }>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ deviceId, data }) => deviceService.updateDevice(deviceId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      queryClient.invalidateQueries({ queryKey: ['devices', variables.deviceId] });
    },
    ...options,
  });
}

export function useDeleteDevice(options?: UseMutationOptions<void, any, string>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (deviceId) => deviceService.deleteDevice(deviceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
    ...options,
  });
}

// ============================================================================
// Deployment Hooks
// ============================================================================

export function useDeployments(params?: any, options?: UseQueryOptions<any>) {
  return useQuery({
    queryKey: ['deployments', params],
    queryFn: () => deploymentService.getDeployments(params),
    ...options,
  });
}

export function useDeployment(deploymentId: string, options?: UseQueryOptions<Deployment>) {
  return useQuery({
    queryKey: ['deployments', deploymentId],
    queryFn: () => deploymentService.getDeployment(deploymentId),
    enabled: !!deploymentId,
    ...options,
  });
}

export function useDeploymentProgress(deploymentId: string, options?: UseQueryOptions<any>) {
  return useQuery({
    queryKey: ['deployments', deploymentId, 'progress'],
    queryFn: () => deploymentService.getDeploymentProgress(deploymentId),
    enabled: !!deploymentId,
    refetchInterval: 5000, // Poll every 5 seconds for active deployments
    ...options,
  });
}

export function useDeploymentStatistics(options?: UseQueryOptions<any>) {
  return useQuery({
    queryKey: ['deployments', 'statistics'],
    queryFn: () => deploymentService.getStatistics(),
    ...options,
  });
}

export function useCreateDeployment(options?: UseMutationOptions<Deployment, any, any>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data) => deploymentService.createDeployment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
    },
    ...options,
  });
}

export function useCancelDeployment(options?: UseMutationOptions<void, any, string>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (deploymentId) => deploymentService.cancelDeployment(deploymentId),
    onSuccess: (_, deploymentId) => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
      queryClient.invalidateQueries({ queryKey: ['deployments', deploymentId] });
    },
    ...options,
  });
}

export function useRollbackDeployment(options?: UseMutationOptions<Deployment, any, string>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (deploymentId) => deploymentService.rollbackDeployment(deploymentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
    },
    ...options,
  });
}

// ============================================================================
// Alert Hooks
// ============================================================================

export function useAlerts(params?: any, options?: UseQueryOptions<any>) {
  return useQuery({
    queryKey: ['alerts', params],
    queryFn: () => alertService.getAlerts(params),
    refetchInterval: 30000, // Poll every 30 seconds for new alerts
    ...options,
  });
}

export function useAlert(alertId: string, options?: UseQueryOptions<Alert>) {
  return useQuery({
    queryKey: ['alerts', alertId],
    queryFn: () => alertService.getAlert(alertId),
    enabled: !!alertId,
    ...options,
  });
}

export function useAcknowledgeAlert(options?: UseMutationOptions<Alert, any, { alertId: string; acknowledgedBy: string }>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ alertId, acknowledgedBy }) => alertService.acknowledgeAlert(alertId, acknowledgedBy),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
    ...options,
  });
}

export function useResolveAlert(options?: UseMutationOptions<Alert, any, string>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (alertId) => alertService.resolveAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
    ...options,
  });
}

// ============================================================================
// Metrics Hooks
// ============================================================================

export function useFleetMetrics(options?: UseQueryOptions<FleetMetrics>) {
  return useQuery({
    queryKey: ['metrics', 'fleet'],
    queryFn: () => metricsService.getFleetMetrics(),
    refetchInterval: 10000, // Poll every 10 seconds
    ...options,
  });
}

export function useFleetMetricsHistory(params: any, options?: UseQueryOptions<FleetMetrics[]>) {
  return useQuery({
    queryKey: ['metrics', 'fleet', 'history', params],
    queryFn: () => metricsService.getFleetMetricsHistory(params),
    ...options,
  });
}

export function useDeviceMetrics(deviceId: string, params: any, options?: UseQueryOptions<any>) {
  return useQuery({
    queryKey: ['metrics', 'devices', deviceId, params],
    queryFn: () => metricsService.getDeviceMetrics(deviceId, params),
    enabled: !!deviceId,
    ...options,
  });
}
