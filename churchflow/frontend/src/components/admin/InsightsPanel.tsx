/**
 * InsightsPanel Component - Phase 7
 *
 * Displays AI-generated insights and alerts for the dashboard.
 */

import React from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

export interface Insight {
  type: 'positive' | 'warning' | 'info';
  title: string;
  message: string;
  priority: 'high' | 'medium' | 'low';
}

export interface Alert {
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  action: string;
}

export interface InsightsPanelProps {
  insights: Insight[];
  alerts: Alert[];
  loading?: boolean;
}

const INSIGHT_STYLES = {
  positive: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    icon: CheckCircleIcon,
    iconColor: 'text-green-600',
    titleColor: 'text-green-900',
  },
  warning: {
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    icon: ExclamationTriangleIcon,
    iconColor: 'text-amber-600',
    titleColor: 'text-amber-900',
  },
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    icon: InformationCircleIcon,
    iconColor: 'text-blue-600',
    titleColor: 'text-blue-900',
  },
};

const ALERT_STYLES = {
  critical: {
    bg: 'bg-red-50',
    border: 'border-red-300',
    icon: XCircleIcon,
    iconColor: 'text-red-600',
    titleColor: 'text-red-900',
    badgeBg: 'bg-red-600',
  },
  warning: {
    bg: 'bg-amber-50',
    border: 'border-amber-300',
    icon: ExclamationTriangleIcon,
    iconColor: 'text-amber-600',
    titleColor: 'text-amber-900',
    badgeBg: 'bg-amber-600',
  },
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-300',
    icon: InformationCircleIcon,
    iconColor: 'text-blue-600',
    titleColor: 'text-blue-900',
    badgeBg: 'bg-blue-600',
  },
};

export const InsightsPanel: React.FC<InsightsPanelProps> = ({
  insights,
  alerts,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="space-y-4">
        <div className="bg-white rounded-lg shadow p-6 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const hasContent = insights.length > 0 || alerts.length > 0;

  if (!hasContent) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Insights & Alerts</h3>
        <p className="text-gray-500 text-center py-8">
          No insights or alerts at this time
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Alerts ({alerts.length})
          </h3>
          <div className="space-y-3">
            {alerts.map((alert, index) => {
              const styles = ALERT_STYLES[alert.severity];
              const Icon = styles.icon;

              return (
                <div
                  key={index}
                  className={`border ${styles.border} ${styles.bg} rounded-lg p-4`}
                >
                  <div className="flex gap-3">
                    <Icon className={`w-5 h-5 ${styles.iconColor} flex-shrink-0 mt-0.5`} />
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className={`font-semibold ${styles.titleColor}`}>{alert.title}</h4>
                        <span
                          className={`${styles.badgeBg} text-white text-xs px-2 py-1 rounded-full uppercase`}
                        >
                          {alert.severity}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mt-1">{alert.message}</p>
                      <p className="text-sm font-medium text-gray-900 mt-2">
                        <span className="text-gray-600">Action:</span> {alert.action}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Insights Section */}
      {insights.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Insights ({insights.length})
          </h3>
          <div className="space-y-3">
            {insights.map((insight, index) => {
              const styles = INSIGHT_STYLES[insight.type];
              const Icon = styles.icon;

              return (
                <div
                  key={index}
                  className={`border ${styles.border} ${styles.bg} rounded-lg p-4`}
                >
                  <div className="flex gap-3">
                    <Icon className={`w-5 h-5 ${styles.iconColor} flex-shrink-0 mt-0.5`} />
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className={`font-semibold ${styles.titleColor}`}>{insight.title}</h4>
                        <span
                          className={`text-xs px-2 py-1 rounded-full border ${styles.border} ${styles.iconColor}`}
                        >
                          {insight.priority}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mt-1">{insight.message}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default InsightsPanel;
