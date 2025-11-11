/**
 * Stat Card Component - Displays statistics with optional trend
 */

import React from 'react';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'gray';
}

const colorClasses = {
  primary: 'bg-primary-50 text-primary-600',
  success: 'bg-success-50 text-success-600',
  warning: 'bg-warning-50 text-warning-600',
  danger: 'bg-danger-50 text-danger-600',
  gray: 'bg-gray-50 text-gray-600',
};

export default function StatCard({ title, value, icon: Icon, trend, color = 'primary' }: StatCardProps) {
  return (
    <div className="card">
      <div className="card-body">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm text-gray-600 mb-1">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {trend && (
              <div className="flex items-center gap-1 mt-2">
                {trend.isPositive ? (
                  <TrendingUp className="w-4 h-4 text-success-600" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-danger-600" />
                )}
                <span
                  className={`text-sm font-medium ${
                    trend.isPositive ? 'text-success-600' : 'text-danger-600'
                  }`}
                >
                  {Math.abs(trend.value)}%
                </span>
              </div>
            )}
          </div>
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </div>
    </div>
  );
}
