import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  BarChart3,
  Heart,
  Phone,
  Rocket,
  Settings,
  TrendingUp
} from 'lucide-react';

export type AnalyticsView =
  | 'automation'
  | 'deployment'
  | 'health'
  | 'vapi'
  | 'system';

interface AnalyticsSidebarProps {
  selectedView: AnalyticsView;
  onViewChange: (view: AnalyticsView) => void;
  className?: string;
}

interface SidebarItem {
  id: AnalyticsView;
  label: string;
  icon: React.ReactNode;
  description: string;
  badge?: string;
}

const sidebarItems: SidebarItem[] = [
  {
    id: 'automation',
    label: 'Automation Overview',
    icon: <TrendingUp className="h-4 w-4" />,
    description: 'Unified automation analytics and monitoring',
    badge: 'Main'
  },
  {
    id: 'deployment',
    label: 'Deployment Metrics',
    icon: <Rocket className="h-4 w-4" />,
    description: 'Track deployment performance and trends'
  },
  {
    id: 'vapi',
    label: 'Voice & VAPI',
    icon: <Phone className="h-4 w-4" />,
    description: 'Voice agent analytics and call metrics'
  },
  {
    id: 'health',
    label: 'Health Monitoring',
    icon: <Heart className="h-4 w-4" />,
    description: 'Real-time system health and component status'
  },
  {
    id: 'system',
    label: 'System Health',
    icon: <Settings className="h-4 w-4" />,
    description: 'Server resources and system performance'
  }
];

const AnalyticsSidebar: React.FC<AnalyticsSidebarProps> = ({
  selectedView,
  onViewChange,
  className
}) => {
  return (
    <div className={cn("w-80 bg-card border-r border-border", className)}>
      <div className="p-6">
        <div className="flex items-center space-x-2 mb-6">
          <BarChart3 className="h-6 w-6 text-indigo-600" />
          <h2 className="text-xl font-bold text-foreground">Analytics</h2>
        </div>

        <nav className="space-y-2">
          {sidebarItems.map((item) => (
            <Button
              key={item.id}
              variant={selectedView === item.id ? "secondary" : "ghost"}
              className={cn(
                "w-full justify-start h-auto p-4 text-left",
                selectedView === item.id
                  ? "bg-primary/10 text-indigo-600 font-medium"
                  : "text-foreground hover:bg-accent"
              )}
              onClick={() => onViewChange(item.id)}
            >
              <div className="flex items-start space-x-3 w-full">
                <div className={cn(
                  "p-1 rounded-md",
                  selectedView === item.id
                    ? "bg-primary/20 text-indigo-600"
                    : "bg-muted text-gray-600"
                )}>
                  {item.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-sm truncate">
                      {item.label}
                    </p>
                    {item.badge && (
                      <Badge
                        variant="secondary"
                        className={cn(
                          "text-xs ml-2",
                          selectedView === item.id
                            ? "bg-primary/20 text-indigo-600"
                            : "bg-muted text-gray-600"
                        )}
                      >
                        {item.badge}
                      </Badge>
                    )}
                  </div>
                  <p className={cn(
                    "text-xs mt-1 line-clamp-2",
                    selectedView === item.id
                      ? "text-primary/80"
                      : "text-gray-600"
                  )}>
                    {item.description}
                  </p>
                </div>
              </div>
            </Button>
          ))}
        </nav>

        <div className="mt-8 p-4 bg-muted rounded-lg">
          <h3 className="font-medium text-sm text-foreground mb-2">
            Quick Access
          </h3>
          <div className="space-y-2 text-sm text-gray-600">
            <button
              className="block hover:text-foreground transition-colors"
              onClick={() => window.open('/call-logs', '_blank')}
            >
              → Call Logs
            </button>
            <button
              className="block hover:text-foreground transition-colors"
              onClick={() => window.open('/admin/system-health', '_blank')}
            >
              → System Health (Admin)
            </button>
            <button
              className="block hover:text-foreground transition-colors"
              onClick={() => window.open('/settings', '_blank')}
            >
              → Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsSidebar;