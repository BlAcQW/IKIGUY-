import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ExternalLink, Settings } from 'lucide-react';
import AnalyticsSidebar, { type AnalyticsView } from '@/components/analytics/AnalyticsSidebar';
import UnifiedAutomationDashboard from '@/components/analytics/UnifiedAutomationDashboard';
import DeploymentAnalyticsDashboard from '@/components/analytics/DeploymentAnalyticsDashboard';
import RealTimeHealthMonitor from '@/components/analytics/RealTimeHealthMonitor';
import VapiAnalyticsDashboard from '@/components/voice-agent/VapiAnalyticsDashboard';
import { API_BASE_URL, CORE_API_URL, buildApiUrl } from '@/config/api-config';


const Analytics: React.FC = () => {
  const { user, isLoading } = useMongoAuth();
  const [selectedView, setSelectedView] = useState<AnalyticsView>('automation');

  if (isLoading) {
    return (
      <div className="flex h-screen bg-gray-50">
        <DashboardSidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading analytics...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  const renderAnalyticsView = () => {
    const tenantId = user.user_metadata?.tenant_id || user.id || '';
    const defaultAutomationId = 'default-automation'; // This should come from user context or props

    switch (selectedView) {
      case 'automation':
        return (
          <UnifiedAutomationDashboard
            timeRange="7d"
            className="h-full"
          />
        );

      case 'deployment':
        return (
          <DeploymentAnalyticsDashboard
            tenantId={tenantId}
          />
        );

      case 'vapi':
        return (
          <VapiAnalyticsDashboard
            agentId={defaultAutomationId}
            tenantId={tenantId}
            apiBaseUrl={API_BASE_URL}
          />
        );

      case 'health':
        return (
          <RealTimeHealthMonitor
            automationId={defaultAutomationId}
            showActivityLog={true}
            refreshInterval={30000}
          />
        );

      case 'system':
        return (
          <Card>
            <CardContent className="flex flex-col items-center justify-center h-96 text-center">
              <Settings className="h-16 w-16 text-gray-600 mb-4" />
              <h3 className="text-xl font-semibold mb-2">System Health Dashboard</h3>
              <p className="text-gray-600 mb-6 max-w-md">
                The system health dashboard is available in the admin section with
                detailed server metrics and resource monitoring.
              </p>
              <Button
                onClick={() => window.open('/admin/system-health', '_blank')}
                className="flex items-center"
              >
                Open System Health Dashboard
                <ExternalLink className="h-4 w-4 ml-2" />
              </Button>
            </CardContent>
          </Card>
        );

      default:
        return (
          <Card>
            <CardContent className="flex items-center justify-center h-96">
              <div className="text-center">
                <h3 className="text-lg font-semibold mb-2">Analytics View</h3>
                <p className="text-gray-600">
                  Select a view from the sidebar to see analytics data
                </p>
              </div>
            </CardContent>
          </Card>
        );
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <DashboardSidebar />
      <div className="flex-1 flex">
        <AnalyticsSidebar
          selectedView={selectedView}
          onViewChange={setSelectedView}
        />
        <main className="flex-1 overflow-y-auto">
          <div className="h-full p-6">
            {renderAnalyticsView()}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Analytics;