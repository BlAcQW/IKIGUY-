import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Users,
  Settings,
  Shield,
  Database,
  Activity,
  FileText,
  Key,
  UserCog,
  Cpu,
  Building2,
  Clock,
  TrendingUp,
  DollarSign,
  Zap,
  AlertTriangle,
  Library,
  Volume2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useOrganization } from '@/contexts/OrganizationContext';

const adminNavItems = [
  { title: 'Organizations', url: '/admin/organizations', icon: Building2, description: 'Manage organizations' },
  { title: 'Users', url: '/admin/users', icon: Users, description: 'Manage user accounts' },
  { title: 'Billing Management', url: '/admin/billing', icon: DollarSign, description: 'Manage billing records' },
  { title: 'Fraud Detection', url: '/admin/fraud', icon: AlertTriangle, description: 'Review flagged transactions' },
  { title: 'Wallet Auto-Reload', url: '/admin/auto-reload', icon: Zap, description: 'Monitor auto-reload' },
  { title: 'Cost Analytics', url: '/admin/cost-analytics', icon: TrendingUp, description: 'Profit margin analysis' },
  { title: 'System Health', url: '/admin/system-health', icon: Activity, description: 'Monitor system resources' },
  { title: 'GPU Monitoring', url: '/admin/gpu', icon: Cpu, description: 'GPU status overview' },
  { title: 'Cron Jobs', url: '/admin/cron', icon: Clock, description: 'Manage scheduled jobs' },
  { title: 'Voice Library', url: '/admin/voice-library', icon: Library, description: 'Manage voice library' },
  { title: 'Voice Settings', url: '/admin/voice-settings', icon: Volume2, description: 'Configure voice settings' },
  { title: 'Roles & Permissions', url: '/admin/roles', icon: Shield, description: 'Configure roles' },
  { title: 'System Settings', url: '/admin/settings', icon: Settings, description: 'System configuration' },
  { title: 'Database', url: '/admin/database', icon: Database, description: 'Database management' },
  { title: 'Activity Logs', url: '/admin/logs', icon: FileText, description: 'View system logs' },
  { title: 'API Keys', url: '/admin/api-keys', icon: Key, description: 'Manage API keys' },
];

const roleColors: Record<string, string> = {
  UNIVERSAL_ADMIN: 'text-purple-600 bg-purple-100 border-purple-300',
  OWNER: 'text-blue-600 bg-blue-100 border-blue-300',
  ADMIN: 'text-green-600 bg-green-100 border-green-300',
};

export function AdminSidebar() {
  const location = useLocation();
  const currentPath = location.pathname;
  const { currentOrganization, isUniversalAdmin, currentRole } = useOrganization();

  const isActive = (path: string) => currentPath === path;

  return (
    <div className="w-64 bg-card border-r border-border h-full flex flex-col">
      {/* Admin Header */}
      <div className="p-6 border-b border-border space-y-4">
        <div className="flex items-center gap-2">
          <UserCog className="h-6 w-6 text-indigo-600" />
          <div>
            <h2 className="text-lg text-heading">Admin Panel</h2>
            <p className="text-xs text-gray-600 text-ui">System Administration</p>
          </div>
        </div>

        {/* Organization Context Banner */}
        {currentOrganization && (
          <div className="bg-accent/50 border border-border rounded-lg p-3 space-y-2">
            <div className="flex items-start gap-2">
              <Building2 className="h-4 w-4 mt-0.5 text-gray-600 flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-xs text-gray-600">Viewing Organization</p>
                <p className="text-sm font-medium text-heading truncate">
                  {currentOrganization.display_name || currentOrganization.name}
                </p>
              </div>
            </div>

            {currentRole && (
              <div className="flex items-center gap-2">
                {isUniversalAdmin && <Shield className="h-3 w-3" />}
                <span className={cn(
                  "text-xs px-2 py-0.5 rounded-full border inline-block",
                  roleColors[currentRole] || 'text-gray-600 bg-gray-100 border-gray-300'
                )}>
                  {currentRole === 'UNIVERSAL_ADMIN' ? 'Universal Admin' : currentRole}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {adminNavItems.map((item) => (
          <Button
            key={item.title}
            variant={isActive(item.url) ? "secondary" : "ghost"}
            className={cn(
              "w-full justify-start gap-3 h-auto py-3 px-3",
              isActive(item.url) && "bg-primary/10 text-indigo-600 font-medium"
            )}
            asChild
          >
            <NavLink to={item.url}>
              <item.icon className="h-4 w-4 flex-shrink-0" />
              <div className="flex flex-col items-start">
                <span className="text-sm text-ui">{item.title}</span>
                <span className="text-xs text-gray-600">{item.description}</span>
              </div>
            </NavLink>
          </Button>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="text-xs text-gray-600">
          <p>Admin Access Level</p>
          <p className="font-medium text-indigo-600">Full System Control</p>
        </div>
      </div>
    </div>
  );
}