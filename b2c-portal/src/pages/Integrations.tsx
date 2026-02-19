import React from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { IntegrationsManagement } from '@/components/integrations/IntegrationsManagement';

const Integrations: React.FC = () => {
  return (
    <div className="min-h-screen bg-background flex">
      <DashboardSidebar />
      <main className="flex-1 overflow-hidden h-screen">
        <IntegrationsManagement />
      </main>
    </div>
  );
};

export default Integrations;