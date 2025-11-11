/**
 * Status Badge Component - Displays colored status badges
 */

import React from 'react';
import type { DeviceStatus, AlertSeverity, DeploymentStatus } from '../../types';
import {
  getStatusBadgeColor,
  getAlertSeverityBadgeColor,
  getDeploymentStatusBadgeColor,
} from '../../utils/status';

interface StatusBadgeProps {
  status: DeviceStatus | AlertSeverity | DeploymentStatus;
  type?: 'device' | 'alert' | 'deployment';
  withDot?: boolean;
}

export default function StatusBadge({ status, type = 'device', withDot = false }: StatusBadgeProps) {
  let colorClass = '';
  let dotColorClass = '';

  if (type === 'device') {
    colorClass = getStatusBadgeColor(status as DeviceStatus);
    dotColorClass = `status-dot-${status}`;
  } else if (type === 'alert') {
    colorClass = getAlertSeverityBadgeColor(status as AlertSeverity);
  } else if (type === 'deployment') {
    colorClass = getDeploymentStatusBadgeColor(status as DeploymentStatus);
  }

  return (
    <span className={`badge ${colorClass}`}>
      {withDot && <span className={`status-dot ${dotColorClass} mr-1.5`} />}
      {status}
    </span>
  );
}
