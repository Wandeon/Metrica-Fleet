/**
 * Settings Page - Application settings and configuration
 */

import React from 'react';
import { Settings as SettingsIcon, Database, Bell, Shield, ExternalLink } from 'lucide-react';
import { Card, CardHeader, CardBody } from '../components/common/Card';

export default function Settings() {
  const apiUrl = import.meta.env.VITE_API_URL || window.REACT_APP_API_URL || 'http://localhost:8080';
  const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || window.REACT_APP_GRAFANA_URL || 'http://localhost:3000';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
        <p className="text-gray-600">Configure your fleet management system</p>
      </div>

      {/* API Configuration */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Database className="w-5 h-5" />
            API Configuration
          </h2>
        </CardHeader>
        <CardBody className="space-y-4">
          <div>
            <label className="label">Fleet API URL</label>
            <input type="text" value={apiUrl} disabled className="input" />
            <p className="text-sm text-gray-600 mt-1">The Fleet Management API endpoint</p>
          </div>
          <div>
            <label className="label">API Key</label>
            <input type="password" value="••••••••••••••••" disabled className="input" />
            <p className="text-sm text-gray-600 mt-1">Authentication key for API access</p>
          </div>
          <div className="flex items-center gap-3 pt-2">
            <a href={`${apiUrl}/docs`} target="_blank" rel="noopener noreferrer" className="btn btn-secondary flex items-center gap-2">
              View API Docs
              <ExternalLink className="w-4 h-4" />
            </a>
            <a href={`${apiUrl}/health`} target="_blank" rel="noopener noreferrer" className="btn btn-secondary">
              Check API Health
            </a>
          </div>
        </CardBody>
      </Card>

      {/* Monitoring Integration */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <SettingsIcon className="w-5 h-5" />
            Monitoring Integration
          </h2>
        </CardHeader>
        <CardBody className="space-y-4">
          <div>
            <label className="label">Grafana URL</label>
            <input type="text" value={grafanaUrl} disabled className="input" />
            <p className="text-sm text-gray-600 mt-1">Grafana dashboard for metrics visualization</p>
          </div>
          <div className="flex items-center gap-3 pt-2">
            <a href={grafanaUrl} target="_blank" rel="noopener noreferrer" className="btn btn-secondary flex items-center gap-2">
              Open Grafana
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </CardBody>
      </Card>

      {/* Alert Configuration */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Alert Configuration
          </h2>
        </CardHeader>
        <CardBody className="space-y-4">
          <div>
            <label className="label">Default Alert Email</label>
            <input type="email" placeholder="admin@example.com" className="input" />
            <p className="text-sm text-gray-600 mt-1">Email address for critical alerts</p>
          </div>
          <div>
            <label className="label">Alert Severity Thresholds</label>
            <div className="space-y-3 mt-2">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">CPU Warning (%)</label>
                  <input type="number" defaultValue="70" className="input mt-1" />
                </div>
                <div>
                  <label className="text-sm text-gray-600">CPU Critical (%)</label>
                  <input type="number" defaultValue="90" className="input mt-1" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Memory Warning (%)</label>
                  <input type="number" defaultValue="75" className="input mt-1" />
                </div>
                <div>
                  <label className="text-sm text-gray-600">Memory Critical (%)</label>
                  <input type="number" defaultValue="90" className="input mt-1" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Disk Warning (%)</label>
                  <input type="number" defaultValue="80" className="input mt-1" />
                </div>
                <div>
                  <label className="text-sm text-gray-600">Disk Critical (%)</label>
                  <input type="number" defaultValue="95" className="input mt-1" />
                </div>
              </div>
            </div>
          </div>
          <div className="pt-2">
            <button className="btn btn-primary">Save Alert Settings</button>
          </div>
        </CardBody>
      </Card>

      {/* System Information */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Shield className="w-5 h-5" />
            System Information
          </h2>
        </CardHeader>
        <CardBody className="space-y-3">
          <div>
            <p className="text-sm text-gray-600">Dashboard Version</p>
            <p className="font-medium">1.0.0</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Build Date</p>
            <p className="font-medium">{new Date().toLocaleDateString()}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Environment</p>
            <p className="font-medium">{import.meta.env.MODE}</p>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
