import QuickAutomationDeployment from "@/components/campaigns/QuickAutomationDeployment";
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';

const QuickDeploy = () => {
  return (
    <div className="flex h-screen bg-background text-foreground">
      <DashboardSidebar />
      <div className="flex-1 overflow-y-auto">
        <QuickAutomationDeployment />
      </div>
    </div>
  );
};

export default QuickDeploy;