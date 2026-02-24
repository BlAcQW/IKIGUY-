import React, { useState, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { logout } from '../lib/auth';
import { useAuth } from '../hooks/useAuth';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Sheet, SheetContent, SheetTitle } from './ui/sheet';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip';
import {
  LayoutDashboard,
  Bot,
  Phone,
  PhoneCall,
  Headphones,
  Settings,
  LogOut,
  Wrench,
  Users,
  Megaphone,
  Bell,
  BarChart3,
  Menu,
  ChevronRight,
  AudioLines,
  Key,
} from 'lucide-react';

const navSections = [
  {
    label: 'Build',
    items: [
      { path: '/assistants', label: 'Assistants', icon: Bot },
      { path: '/squads', label: 'Squads', icon: Users },
      { path: '/tools', label: 'Tools', icon: Wrench },
      { path: '/phone-numbers', label: 'Phone Numbers', icon: Phone },
      { path: '/voice-library', label: 'Voice Library', icon: AudioLines },
      { path: '/api-keys', label: 'API Keys', icon: Key },
    ],
  },
  {
    label: 'Test',
    items: [
      { path: '/web-call', label: 'Web Call', icon: Headphones, accent: true },
    ],
  },
  {
    label: 'Observe',
    items: [
      { path: '/', label: 'Dashboard', icon: LayoutDashboard },
      { path: '/calls', label: 'Call Logs', icon: PhoneCall },
      { path: '/analytics', label: 'Analytics', icon: BarChart3 },
    ],
  },
  {
    label: 'Manage',
    items: [
      { path: '/campaigns', label: 'Campaigns', icon: Megaphone },
      { path: '/webhooks', label: 'Webhooks', icon: Bell },
      { path: '/settings', label: 'Settings', icon: Settings },
    ],
  },
];

function BrandLogo() {
  return (
    <div className="flex items-center gap-3">
      <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center relative overflow-hidden">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-primary relative z-10">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="currentColor" />
        </svg>
      </div>
      <div>
        <h1 className="text-base font-display font-bold tracking-tight text-foreground leading-none">LOAD</h1>
        <p className="text-[10px] text-muted-foreground leading-tight mt-0.5 tracking-wide uppercase">Voice AI</p>
      </div>
    </div>
  );
}

function UserAvatar({ name }: { name?: string }) {
  const initials = name
    ? name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : '?';
  return (
    <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 text-primary flex items-center justify-center text-[11px] font-semibold shrink-0">
      {initials}
    </div>
  );
}

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const location = useLocation();
  const { user } = useAuth();

  return (
    <div className="flex flex-col h-full bg-sidebar text-sidebar-foreground relative">
      {/* Subtle noise texture */}
      <div className="absolute inset-0 noise-overlay pointer-events-none" />

      {/* Brand */}
      <div className="px-5 pt-6 pb-5 relative z-10">
        <BrandLogo />
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 pb-3 overflow-y-auto scrollbar-thin relative z-10">
        {navSections.map((section) => (
          <div key={section.label} className="mb-4">
            <div className="px-3 mb-1.5">
              <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
                {section.label}
              </span>
            </div>
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = item.path === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={onNavigate}
                  className={`group flex items-center gap-3 px-3 py-2 rounded-lg mb-0.5 text-[13px] transition-all duration-150 relative ${
                    isActive
                      ? 'bg-primary/10 text-primary font-medium'
                      : 'text-muted-foreground hover:text-sidebar-foreground hover:bg-white/[0.03]'
                  }`}
                >
                  {isActive && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-4 bg-primary rounded-r-full" />
                  )}
                  <Icon size={16} className={isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-sidebar-foreground'} />
                  <span className="flex-1">{item.label}</span>
                  {'accent' in item && item.accent && !isActive && (
                    <div className="w-1.5 h-1.5 rounded-full bg-primary/60" />
                  )}
                  {isActive && (
                    <ChevronRight size={12} className="text-primary/60" />
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* User section */}
      <div className="border-t border-sidebar-border p-3 relative z-10">
        {user && (
          <div className="flex items-center gap-3 px-2 py-2.5 rounded-lg mb-2">
            <UserAvatar name={user.name} />
            <div className="min-w-0 flex-1">
              <p className="text-[13px] font-medium text-sidebar-foreground truncate">
                {user.name || user.email || 'User'}
              </p>
              <p className="text-[11px] text-muted-foreground truncate">
                {user.organizationName || 'Organization'}
              </p>
            </div>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="shrink-0">
                    <Badge variant="outline" className="text-[9px] px-1.5 py-0 border-sidebar-border text-muted-foreground font-medium tracking-wide uppercase">
                      {user.role === 'OWNER' ? 'Owner' : user.role === 'ADMIN' ? 'Admin' : 'Member'}
                    </Badge>
                  </span>
                </TooltipTrigger>
                <TooltipContent side="top">
                  <p>{user.role} role</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        )}
        <Button
          variant="ghost"
          onClick={logout}
          className="w-full justify-start gap-3 text-muted-foreground hover:text-destructive hover:bg-destructive/5 text-[13px] h-9"
          size="sm"
        >
          <LogOut size={14} />
          Sign out
        </Button>
      </div>
    </div>
  );
}

export function Layout({ children, noPadding = false }: { children: React.ReactNode; noPadding?: boolean }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const handleNavigate = useCallback(() => setMobileOpen(false), []);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile hamburger */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 bg-background/80 backdrop-blur-xl border-b px-4 py-3 flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => setMobileOpen(true)} className="h-8 w-8">
          <Menu size={18} />
        </Button>
        <BrandLogo />
      </div>

      {/* Mobile sheet sidebar */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="p-0 w-[280px] bg-sidebar border-sidebar-border">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SidebarNav onNavigate={handleNavigate} />
        </SheetContent>
      </Sheet>

      {/* Desktop sidebar */}
      <aside className="hidden md:block w-[260px] border-r border-sidebar-border shrink-0 bg-sidebar">
        <SidebarNav />
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto scrollbar-thin bg-background">
        {noPadding ? (
          children
        ) : (
          <div className="p-6 md:px-8 md:py-8 pt-16 md:pt-8 max-w-[1400px]">
            {children}
          </div>
        )}
      </main>
    </div>
  );
}
