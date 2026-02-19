import React from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle, ArrowRight, BarChart3, Settings } from 'lucide-react';

const AutomationSuccess: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />
      
      <div className="flex-1 overflow-auto">
        <div className="container mx-auto p-6 flex items-center justify-center min-h-[60vh]">
          <Card className="max-w-md w-full text-center">
        <CardHeader className="pb-4">
          <div className="mx-auto mb-4 w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
            <CheckCircle className="h-10 w-10 text-green-600" />
          </div>
          <CardTitle className="text-2xl text-green-700">Automation Deployed!</CardTitle>
          <CardDescription>
            Your automation has been successfully configured and is now active
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm text-gray-600">
              Your automation is now running and will begin processing according to your configured triggers and schedules.
            </p>
          </div>
          
          <div className="flex flex-col gap-2 pt-4">
            <Button onClick={() => navigate('/automations')} className="w-full">
              <ArrowRight className="h-4 w-4 mr-2" />
              Back to Automations
            </Button>
            
            <Button variant="outline" onClick={() => navigate('/analytics')} className="w-full">
              <BarChart3 className="h-4 w-4 mr-2" />
              View Analytics
            </Button>
            
            <Button variant="outline" onClick={() => navigate('/settings')} className="w-full">
              <Settings className="h-4 w-4 mr-2" />
              Manage Settings
            </Button>
          </div>
        </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AutomationSuccess;