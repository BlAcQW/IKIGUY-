/**
 * BottomNav Component
 * Mobile-first bottom navigation bar inspired by YouVersion Bible app
 */

import { Link, useLocation } from 'react-router-dom';
import { Home, Compass, Bookmark, User, MessageCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  activePattern: RegExp;
}

const navItems: NavItem[] = [
  {
    id: 'today',
    label: 'Today',
    icon: <Home className="w-6 h-6" />,
    path: '/today',
    activePattern: /^\/(today)?$/,
  },
  {
    id: 'discover',
    label: 'Discover',
    icon: <Compass className="w-6 h-6" />,
    path: '/feed',
    activePattern: /^\/(feed|devotional\/.*)/,
  },
  {
    id: 'discussions',
    label: 'Discussions',
    icon: <MessageCircle className="w-6 h-6" />,
    path: '/discussions',
    activePattern: /^\/discussions/,
  },
  {
    id: 'saved',
    label: 'Saved',
    icon: <Bookmark className="w-6 h-6" />,
    path: '/bookmarks',
    activePattern: /^\/bookmarks/,
  },
  {
    id: 'profile',
    label: 'Profile',
    icon: <User className="w-6 h-6" />,
    path: '/profile',
    activePattern: /^\/profile/,
  },
];

export function BottomNav() {
  const location = useLocation();

  const isActive = (item: NavItem) => {
    return item.activePattern.test(location.pathname);
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-background/95 backdrop-blur-lg border-t border-border safe-area-bottom">
      <div className="container mx-auto px-2">
        <div className="flex items-center justify-around h-16">
          {navItems.map((item) => {
            const active = isActive(item);
            return (
              <Link
                key={item.id}
                to={item.path}
                className={cn(
                  'flex flex-col items-center justify-center gap-1 px-4 py-2 rounded-lg transition-all',
                  'hover:bg-secondary/10 active:scale-95',
                  active
                    ? 'text-secondary'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                <div
                  className={cn(
                    'transition-transform',
                    active && 'scale-110'
                  )}
                >
                  {item.icon}
                </div>
                <span
                  className={cn(
                    'text-xs font-medium transition-all',
                    active && 'font-semibold'
                  )}
                >
                  {item.label}
                </span>
                {active && (
                  <div className="absolute -bottom-px left-1/2 -translate-x-1/2 w-12 h-0.5 bg-secondary rounded-full" />
                )}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
