import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { HelpIcon } from '@/components/ui/help-icon';
import { HelpModal } from '@/components/ui/help-modal';
import { useHelp } from '@/hooks/useHelp';
import { getHelpContent } from '@/lib/help-content';
import { 
  Bot, 
  MessageSquare, 
  Users, 
  TrendingUp,
  Settings,
  CreditCard,
  HelpCircle
} from 'lucide-react';

/**
 * Comprehensive example demonstrating help integration throughout the B2C portal
 * This component shows how to use help icons, tooltips, and modals in different contexts
 */
export const HelpIntegrationExample: React.FC = () => {
  const help = useHelp();

  // Get help content for different sections
  const dashboardHelp = getHelpContent('dashboard_overview');
  const assistantsHelp = getHelpContent('assistants_overview');
  const integrationsHelp = getHelpContent('integrations_overview');
  const analyticsHelp = getHelpContent('analytics_overview');
  const settingsHelp = getHelpContent('settings_overview');
  const billingHelp = getHelpContent('billing_overview');

  return (
    <div className="space-y-8">
      {/* Page Header with Help Icon */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div>
            <h1 className="text-3xl font-bold text-foreground">
              Help Integration Examples
            </h1>
            <p className="text-gray-600 mt-1">
              Demonstrating comprehensive help system integration
            </p>
          </div>
          {dashboardHelp && (
            <HelpIcon 
              content={dashboardHelp} 
              size="sm" 
              variant="both" 
              position="bottom"
            />
          )}
        </div>
        <Button 
          onClick={() => help.openHelpModal('support_overview')}
          variant="outline"
          className="gap-2"
        >
          <HelpCircle className="h-4 w-4" />
          Open Help Center
        </Button>
      </div>

      {/* Stats Cards with Help Icons */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              Total Assistants
              {assistantsHelp && (
                <HelpIcon 
                  content={assistantsHelp} 
                  size="sm" 
                  variant="tooltip" 
                  position="top"
                />
              )}
            </CardTitle>
            <Bot className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-gray-600">
              Active assistants
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              Active Campaigns
              {analyticsHelp && (
                <HelpIcon 
                  content={analyticsHelp} 
                  size="sm" 
                  variant="tooltip" 
                  position="top"
                />
              )}
            </CardTitle>
            <MessageSquare className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">5</div>
            <p className="text-xs text-gray-600">
              Currently running
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Contacts Reached</CardTitle>
            <Users className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2,847</div>
            <p className="text-xs text-gray-600">
              Total messages sent
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">94%</div>
            <p className="text-xs text-gray-600">
              Message success rate
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Feature Sections with Help */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Integrations Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Integrations
              {integrationsHelp && (
                <HelpIcon 
                  content={integrationsHelp} 
                  size="sm" 
                  variant="both" 
                  position="right"
                />
              )}
            </CardTitle>
            <CardDescription>
              Connect with your favorite tools and platforms
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">HubSpot CRM</span>
              <Badge className="bg-green-500 text-green-50">Connected</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Stripe Payments</span>
              <Badge className="bg-green-500 text-green-50">Connected</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">WhatsApp Business</span>
              <Badge variant="outline">Available</Badge>
            </div>
            <Button variant="outline" size="sm" className="w-full mt-2">
              Manage Integrations
            </Button>
          </CardContent>
        </Card>

        {/* Billing Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Billing & Usage
              {billingHelp && (
                <HelpIcon 
                  content={billingHelp} 
                  size="sm" 
                  variant="both" 
                  position="right"
                />
              )}
            </CardTitle>
            <CardDescription>
              Monitor your usage and manage billing
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm">Current Plan</span>
              <Badge variant="secondary">Professional</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Monthly Usage</span>
              <span className="text-sm font-medium">2,847 / 5,000 messages</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Next Billing</span>
              <span className="text-sm">March 15, 2024</span>
            </div>
            <Button variant="outline" size="sm" className="w-full mt-2">
              View Billing Details
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Help Modal */}
      <HelpModal
        isOpen={help.isHelpModalOpen}
        onClose={help.closeHelpModal}
        initialContent={help.currentHelpContent}
        recentHelp={help.recentHelp}
        onHelpClick={help.openHelpModal}
      />

      {/* Usage Examples */}
      <Card>
        <CardHeader>
          <CardTitle>Help Integration Usage Examples</CardTitle>
          <CardDescription>
            Different ways to use help icons and tooltips
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Tooltip Only */}
            <div className="text-center p-4 border rounded-lg">
              <h4 className="font-medium mb-2">Tooltip Only</h4>
              <p className="text-sm text-gray-600 mb-3">
                Quick help information on hover
              </p>
              {dashboardHelp && (
                <HelpIcon 
                  content={dashboardHelp} 
                  size="sm" 
                  variant="tooltip" 
                  position="top"
                />
              )}
            </div>

            {/* Modal Only */}
            <div className="text-center p-4 border rounded-lg">
              <h4 className="font-medium mb-2">Modal Only</h4>
              <p className="text-sm text-gray-600 mb-3">
                Detailed help in a modal dialog
              </p>
              {assistantsHelp && (
                <HelpIcon 
                  content={assistantsHelp} 
                  size="sm" 
                  variant="modal" 
                  position="top"
                />
              )}
            </div>

            {/* Both Tooltip and Modal */}
            <div className="text-center p-4 border rounded-lg">
              <h4 className="font-medium mb-2">Both Tooltip & Modal</h4>
              <p className="text-sm text-gray-600 mb-3">
                Quick info + detailed help
              </p>
              {integrationsHelp && (
                <HelpIcon 
                  content={integrationsHelp} 
                  size="sm" 
                  variant="both" 
                  position="top"
                />
              )}
            </div>
          </div>

          {/* Different Sizes */}
          <div className="border-t pt-4">
            <h4 className="font-medium mb-3">Different Sizes</h4>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-sm">Small:</span>
                {dashboardHelp && (
                  <HelpIcon 
                    content={dashboardHelp} 
                    size="sm" 
                    variant="tooltip" 
                  />
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm">Medium:</span>
                {dashboardHelp && (
                  <HelpIcon 
                    content={dashboardHelp} 
                    size="md" 
                    variant="tooltip" 
                  />
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm">Large:</span>
                {dashboardHelp && (
                  <HelpIcon 
                    content={dashboardHelp} 
                    size="lg" 
                    variant="tooltip" 
                  />
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
