import React from 'react';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { HelpdeskDashboard as HelpdeskDashboardComponent } from '@/components/dashboard/HelpdeskDashboard';

const HelpdeskDashboard: React.FC = () => {
  return (
    <div className="flex h-screen bg-gray-50">
      <DashboardSidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="container mx-auto py-6 px-4">
          <HelpdeskDashboardComponent />
        </div>
      </main>
    </div>
  );
};

export default HelpdeskDashboard;