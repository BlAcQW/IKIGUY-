import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { 
  Search,
  Bot,
  MessageSquare,
  Mail,
  CreditCard,
  Users,
  HeadphonesIcon,
  Database,
  BarChart3,
  Zap,
  Briefcase,
  Heart,
  Building2,
  Activity,
  Landmark,
  Filter,
  CheckCircle,
  AlertCircle,
  Clock,
  Eye,
  EyeOff
} from 'lucide-react';

interface Integration {
  id: string;
  name: string;
  category: string;
  isConfigured: boolean;
  status: 'configured' | 'not_configured' | 'error';
  isTested: boolean;
}

interface IntegrationCategory {
  id: string;
  name: string;
  icon: React.ElementType;
  description: string;
  color: string;
  count: number;
}

interface IntegrationCategorySidebarProps {
  integrations: Integration[];
  selectedCategory: string | null;
  onCategorySelect: (category: string | null) => void;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  showConfiguredOnly: boolean;
  onShowConfiguredOnlyChange: (show: boolean) => void;
}

const categoryConfig = {
  llm: { name: 'AI Models', icon: Bot, description: 'Large Language Models and AI Services', color: 'bg-orange-100 text-orange-800 border-orange-200' },
  tts: { name: 'Text-to-Speech', icon: MessageSquare, description: 'Voice synthesis and audio generation', color: 'bg-blue-100 text-blue-800 border-blue-200' },
  stt: { name: 'Speech-to-Text', icon: MessageSquare, description: 'Speech recognition and transcription', color: 'bg-purple-100 text-purple-800 border-purple-200' },
  messaging: { name: 'Messaging', icon: MessageSquare, description: 'SMS, WhatsApp, and chat platforms', color: 'bg-pink-100 text-pink-800 border-pink-200' },
  email: { name: 'Email', icon: Mail, description: 'Email delivery and marketing platforms', color: 'bg-indigo-100 text-indigo-800 border-indigo-200' },
  payment: { name: 'Payments', icon: CreditCard, description: 'Payment processing and financial services', color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  crm: { name: 'CRM & Sales', icon: Users, description: 'Customer relationship management tools', color: 'bg-cyan-100 text-cyan-800 border-cyan-200' },
  support: { name: 'Support', icon: HeadphonesIcon, description: 'Customer service and helpdesk platforms', color: 'bg-amber-100 text-amber-800 border-amber-200' },
  storage: { name: 'Storage', icon: Database, description: 'Cloud storage and document management', color: 'bg-slate-100 text-slate-800 border-slate-200' },
  analytics: { name: 'Analytics', icon: BarChart3, description: 'Data analytics and reporting tools', color: 'bg-violet-100 text-violet-800 border-violet-200' },
  automation: { name: 'Automation', icon: Zap, description: 'Workflow automation and integration platforms', color: 'bg-rose-100 text-rose-800 border-rose-200' },
  productivity: { name: 'Productivity', icon: Briefcase, description: 'Office suites and collaboration tools', color: 'bg-blue-100 text-blue-800 border-blue-200' },
  healthcare: { name: 'Healthcare', icon: Heart, description: 'Electronic health records and medical systems', color: 'bg-red-100 text-red-800 border-red-200' },
  enterprise: { name: 'Enterprise', icon: Building2, description: 'Enterprise resource planning and business systems', color: 'bg-gray-100 text-gray-800 border-gray-200' },
  monitoring: { name: 'Monitoring', icon: Activity, description: 'System monitoring and alerting platforms', color: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
  banking: { name: 'Banking', icon: Landmark, description: 'Banking and financial institution integrations', color: 'bg-green-100 text-green-800 border-green-200' },
  telephony: { name: 'Telephony', icon: MessageSquare, description: 'Voice and telephony services', color: 'bg-green-100 text-green-800 border-green-200' }
};

export const IntegrationCategorySidebar: React.FC<IntegrationCategorySidebarProps> = ({
  integrations,
  selectedCategory,
  onCategorySelect,
  searchTerm,
  onSearchChange,
  showConfiguredOnly,
  onShowConfiguredOnlyChange
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Calculate category statistics
  const categories: IntegrationCategory[] = Object.entries(categoryConfig).map(([id, config]) => {
    const categoryIntegrations = integrations.filter(integration => integration.category === id);
    return {
      id,
      name: config.name,
      icon: config.icon,
      description: config.description,
      color: config.color,
      count: categoryIntegrations.length
    };
  }).filter(category => category.count > 0).sort((a, b) => b.count - a.count);

  const getStatusCounts = (categoryId: string) => {
    const categoryIntegrations = integrations.filter(integration => integration.category === categoryId);
    const configured = categoryIntegrations.filter(integration => integration.isConfigured).length;
    const tested = categoryIntegrations.filter(integration => integration.isTested).length;
    const errors = categoryIntegrations.filter(integration => integration.status === 'error').length;
    
    return { configured, tested, errors, total: categoryIntegrations.length };
  };

  const totalIntegrations = integrations.length;
  const configuredIntegrations = integrations.filter(i => i.isConfigured).length;
  const testedIntegrations = integrations.filter(i => i.isTested).length;

  return (
    <div className={cn(
      "bg-card border-r border-border h-full flex flex-col transition-all duration-300",
      isCollapsed ? "w-16" : "w-80"
    )}>
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div>
              <h2 className="text-lg font-semibold">Integration Categories</h2>
              <p className="text-sm text-gray-600">Browse by category</p>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setIsCollapsed(!isCollapsed)}
          >
            {isCollapsed ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
          </Button>
        </div>
        
        {!isCollapsed && (
          <>
            {/* Search */}
            <div className="relative mt-4">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
              <Input
                placeholder="Search integrations..."
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Filters */}
            <div className="mt-4 space-y-2">
              <Button
                variant={showConfiguredOnly ? "default" : "outline"}
                size="sm"
                onClick={() => onShowConfiguredOnlyChange(!showConfiguredOnly)}
                className="w-full justify-start"
              >
                <Filter className="h-4 w-4 mr-2" />
                Configured Only
              </Button>
            </div>
          </>
        )}
      </div>

      {/* Overview Stats */}
      {!isCollapsed && (
        <div className="p-4 border-b border-border">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Total Integrations</span>
              <Badge variant="secondary">{totalIntegrations}</Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 flex items-center gap-1">
                <CheckCircle className="h-3 w-3 text-green-500" />
                Configured
              </span>
              <Badge className="bg-green-100 text-green-800">{configuredIntegrations}</Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 flex items-center gap-1">
                <CheckCircle className="h-3 w-3 text-blue-500" />
                Tested
              </span>
              <Badge className="bg-blue-100 text-blue-800">{testedIntegrations}</Badge>
            </div>
          </div>
        </div>
      )}

      {/* Categories */}
      <div className="flex-1 overflow-auto">
        <div className="p-2">
          {/* All Categories Button */}
          <Button
            variant={selectedCategory === null ? "secondary" : "ghost"}
            className={cn(
              "w-full justify-start mb-2",
              isCollapsed ? "px-0" : ""
            )}
            onClick={() => onCategorySelect(null)}
          >
            <BarChart3 className="h-4 w-4" />
            {!isCollapsed && (
              <>
                <span className="ml-2">All Categories</span>
                <Badge variant="outline" className="ml-auto">
                  {totalIntegrations}
                </Badge>
              </>
            )}
          </Button>

          <Separator className="my-2" />

          {/* Category List */}
          <div className="space-y-1">
            {categories.map((category) => {
              const IconComponent = category.icon;
              const statusCounts = getStatusCounts(category.id);
              const isSelected = selectedCategory === category.id;

              if (isCollapsed) {
                return (
                  <div key={category.id} className="relative">
                    <Button
                      variant={isSelected ? "secondary" : "ghost"}
                      className="w-full p-2 h-auto justify-center relative group"
                      onClick={() => onCategorySelect(category.id)}
                      title={`${category.name} (${category.count})`}
                    >
                      <IconComponent className="h-4 w-4" />
                      {statusCounts.configured > 0 && (
                        <div className="absolute -top-1 -right-1 h-3 w-3 bg-green-500 rounded-full flex items-center justify-center">
                          <span className="text-[10px] text-white font-bold">
                            {statusCounts.configured}
                          </span>
                        </div>
                      )}
                    </Button>
                  </div>
                );
              }

              return (
                <Button
                  key={category.id}
                  variant={isSelected ? "secondary" : "ghost"}
                  className="w-full justify-start p-3 h-auto"
                  onClick={() => onCategorySelect(category.id)}
                >
                  <div className="flex items-center w-full">
                    <IconComponent className="h-4 w-4 flex-shrink-0" />
                    <div className="ml-3 flex-1 text-left">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{category.name}</span>
                        <Badge variant="outline" className="text-xs">
                          {category.count}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        {statusCounts.configured > 0 && (
                          <div className="flex items-center gap-1">
                            <CheckCircle className="h-3 w-3 text-green-500" />
                            <span className="text-xs text-green-600">{statusCounts.configured}</span>
                          </div>
                        )}
                        {statusCounts.tested > 0 && (
                          <div className="flex items-center gap-1">
                            <CheckCircle className="h-3 w-3 text-blue-500" />
                            <span className="text-xs text-blue-600">{statusCounts.tested}</span>
                          </div>
                        )}
                        {statusCounts.errors > 0 && (
                          <div className="flex items-center gap-1">
                            <AlertCircle className="h-3 w-3 text-red-500" />
                            <span className="text-xs text-red-600">{statusCounts.errors}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </Button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Footer with category count */}
      {!isCollapsed && (
        <div className="p-4 border-t border-border">
          <div className="text-xs text-gray-600 text-center">
            {categories.length} categories available
          </div>
        </div>
      )}
    </div>
  );
};