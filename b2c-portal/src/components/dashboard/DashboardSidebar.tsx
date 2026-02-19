import React, { useState, useMemo } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Users,
  BarChart3,
  CreditCard,
  Settings,
  Plug,
  BookOpen,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Menu,
  Microscope,
  Shield,
  Activity,
  Megaphone,
  Zap,
  Rocket,
  Phone,
  Database,
  Mic2,
  Mic,
  MessageCircle,
  Wrench,
  GitCompare,
  PhoneCall,
  TrendingUp
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { LogoutButton } from '@/components/auth/LogoutButton';
import { useMongoAuth } from '@/components/auth/MongoAuthContext';
import { useOrganization } from '@/contexts/OrganizationContext';
import { OrganizationSwitcher } from '@/components/organization/OrganizationSwitcher';
import { ThemeToggle, ThemeToggleCompact } from '@/components/ui/theme-toggle';

const navItems = [
  { title: 'Dashboard', url: '/dashboard', icon: LayoutDashboard, emoji: '📊', requiresUniversalAdmin: true },
  { title: 'Voice Agent', url: '/voice-agent', icon: Bot, emoji: '🤖', requiresUniversalAdmin: true },
  { title: 'Quick Deploy', url: '/quick-deploy', icon: Rocket, emoji: '🚀', requiresUniversalAdmin: true },
  { title: 'Call Logs', url: '/call-logs', icon: Phone, emoji: '📞', requiresUniversalAdmin: false },
  { title: 'Audiences', url: '/audiences', icon: Users, emoji: '👥', requiresUniversalAdmin: false },
  { title: 'SMS Campaigns', url: '/sms-campaigns', icon: MessageSquare, emoji: '📱', requiresUniversalAdmin: false },
  { title: 'WhatsApp Campaigns', url: '/whatsapp-campaigns', icon: MessageCircle, emoji: '💬', requiresUniversalAdmin: false },
  { title: 'Automations', url: '/automations', icon: Zap, emoji: '⚡', requiresUniversalAdmin: false },
  { title: 'Knowledge Base', url: '/knowledge-base', icon: Database, emoji: '📚', requiresUniversalAdmin: false },
  { title: 'Custom Tools', url: '/custom-tools', icon: Plug, emoji: '🔧', requiresUniversalAdmin: false },
  { title: 'Utilities', url: '/utilities', icon: Wrench, emoji: '🛠️', requiresUniversalAdmin: false },
  { title: 'Phone Numbers', url: '/phone-numbers', icon: MessageSquare, emoji: '📱', requiresUniversalAdmin: false },
  { title: 'Telephony', url: '/telephony', icon: PhoneCall, emoji: '☎️', requiresUniversalAdmin: true },
  { title: 'Voice Library', url: '/voice-library', icon: BookOpen, emoji: '🎙️', requiresUniversalAdmin: true },
  { title: 'Voice Lab', url: '/voice-lab', icon: Microscope, emoji: '🔬', requiresUniversalAdmin: true },
  { title: 'Voice Lab Enhanced', url: '/voice-lab-enhanced', icon: Microscope, emoji: '✨', requiresUniversalAdmin: true },
  { title: 'TTS Lab', url: '/tts-lab', icon: Mic2, emoji: '🎵', requiresUniversalAdmin: true },
  { title: 'ASR Lab', url: '/asr-lab', icon: Mic, emoji: '🎤', requiresUniversalAdmin: true },
  { title: 'LLM Lab', url: '/llm-lab', icon: MessageCircle, emoji: '💬', requiresUniversalAdmin: true },
  { title: 'Speech-to-Speech', url: '/speech-to-speech', icon: GitCompare, emoji: '🔄', requiresUniversalAdmin: true },
  { title: 'Vapi Management', url: '/vapi-management', icon: Phone, emoji: '☎️', requiresUniversalAdmin: true },
  { title: 'Analytics', url: '/analytics', icon: BarChart3, emoji: '📈', requiresUniversalAdmin: false },
  { title: 'Affiliates', url: '/affiliates/dashboard', icon: TrendingUp, emoji: '💰', requiresUniversalAdmin: false },
  { title: 'Billing', url: '/billing', icon: CreditCard, emoji: '💳', requiresUniversalAdmin: true },
  { title: 'Integrations', url: '/integrations', icon: Plug, emoji: '🔌', requiresUniversalAdmin: true },
  { title: 'Admin', url: '/admin', icon: Shield, emoji: '🛡️', requiresUniversalAdmin: false },
  { title: 'Settings', url: '/settings', icon: Settings, emoji: '⚙️', requiresUniversalAdmin: false },
  { title: 'Help', url: '/help', icon: HelpCircle, emoji: '❓', requiresUniversalAdmin: false },
];

export function DashboardSidebar() {
  const location = useLocation();
  const currentPath = location.pathname;
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { user } = useMongoAuth();
  const { canAccessAdmin } = useOrganization();

  // Filter menu items based on user role
  const filteredNavItems = useMemo(() => {
    const isUniversalAdmin = user?.is_universal_admin ?? false;

    return navItems.filter(item => {
      // Special handling for Admin link - only show if user has admin access
      if (item.url === '/admin') {
        return canAccessAdmin;
      }

      // If item requires universal_admin, only show to universal admins
      if (item.requiresUniversalAdmin) {
        return isUniversalAdmin;
      }
      // Otherwise, show to everyone
      return true;
    });
  }, [user, canAccessAdmin]);

  const isActive = (path: string) => {
    // Handle exact matches
    if (currentPath === path) return true;
    // Handle affiliates routes - highlight if on any affiliate page
    if (path === '/affiliates/dashboard' && currentPath.startsWith('/affiliates')) return true;
    return false;
  };

  return (
    <TooltipProvider delayDuration={0}>
      <div className={cn(
        "bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 h-screen sticky top-0 flex flex-col transition-all duration-300",
        isCollapsed ? "w-16" : "w-64"
      )}>
        {/* Logo, Organization Switcher, and Collapse Button */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 space-y-3">
          {/* Logo and Collapse Button */}
          <div className="flex items-center justify-between">
            <div className={cn(
              "flex items-center gap-2",
              isCollapsed && "justify-center"
            )}>
              <div className="w-8 h-8 bg-indigo-600 dark:bg-indigo-500 rounded-lg flex items-center justify-center flex-shrink-0">
                <Bot className="h-5 w-5 text-white" />
              </div>
              {!isCollapsed && (
                <span className="text-xl font-bold text-gray-900 dark:text-gray-100">
                  KasaAI
                </span>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "h-8 w-8",
                isCollapsed && "absolute -right-3 top-6 z-10 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm"
              )}
              onClick={() => setIsCollapsed(!isCollapsed)}
            >
              {isCollapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Organization Switcher - Header Location */}
          {!isCollapsed && (
            <div>
              <OrganizationSwitcher variant="compact" />
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {filteredNavItems.map((item) => (
            isCollapsed ? (
              <Tooltip key={item.title}>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    className={cn(
                      "w-full h-10 p-0 justify-center",
                      isActive(item.url) && "bg-indigo-50 text-indigo-600 font-medium"
                    )}
                    asChild
                  >
                    <NavLink to={item.url}>
                      <span className="text-sm">{item.emoji}</span>
                    </NavLink>
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">
                  {item.title}
                </TooltipContent>
              </Tooltip>
            ) : (
              <Button
                key={item.title}
                variant="ghost"
                className={cn(
                  "w-full justify-start gap-3 h-10 rounded-lg transition-all",
                  isActive(item.url)
                    ? "bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-medium border-l-2 border-indigo-500"
                    : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                )}
                asChild
              >
                <NavLink to={item.url}>
                  <span className="text-sm">{item.emoji}</span>
                  {item.title}
                </NavLink>
              </Button>
            )
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
          {/* Theme Toggle */}
          <div>
            {isCollapsed ? (
              <ThemeToggle className="w-full" />
            ) : (
              <ThemeToggleCompact />
            )}
          </div>

          {/* Logout Button */}
          <div>
            {isCollapsed ? (
              <Tooltip>
                <TooltipTrigger asChild>
                  <LogoutButton
                    variant="ghost"
                    size="icon"
                    showIcon={true}
                    className="w-full h-10 p-0 justify-center"
                  />
                </TooltipTrigger>
                <TooltipContent side="right">
                  Logout
                </TooltipContent>
              </Tooltip>
            ) : (
              <LogoutButton
                variant="ghost"
                size="default"
                showIcon={true}
                className="w-full justify-start gap-3 h-10"
                confirmLogout={true}
              />
            )}
          </div>

          {/* Version */}
          {!isCollapsed && (
            <p className="text-xs text-gray-600 dark:text-gray-400 text-center">
              KasaAI v1.0.0
            </p>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}