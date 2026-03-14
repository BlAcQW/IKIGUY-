import {
  LayoutDashboard,
  Bot,
  Phone,
  PhoneCall,
  Headphones,
  Settings,
  Wrench,
  Users,
  Megaphone,
  Bell,
  BarChart3,
  AudioLines,
  Key,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
  accent?: boolean;
}

export interface NavSection {
  label: string;
  items: NavItem[];
}

export const navSections: NavSection[] = [
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
