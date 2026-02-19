/**
 * Mobile Bottom Navigation
 *
 * Bottom navigation bar for mobile devices with 5 tabs:
 * - Home: Property listings
 * - Map: Interactive map view
 * - Saved: Favorites (login required)
 * - Chat: AI property assistant
 * - Account: User profile/settings
 */

import { useNavigate, useLocation } from "react-router-dom";
import { Home, Map, Heart, MessageCircle, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";

interface NavItem {
  id: string;
  label: string;
  icon: typeof Home;
  path: string;
  requiresAuth?: boolean;
  badge?: number;
}

export function MobileBottomNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const navItems: NavItem[] = [
    {
      id: "home",
      label: "Home",
      icon: Home,
      path: "/properties",
    },
    {
      id: "map",
      label: "Map",
      icon: Map,
      path: "/map",
    },
    {
      id: "saved",
      label: "Saved",
      icon: Heart,
      path: "/saved",
      requiresAuth: true,
    },
    {
      id: "chat",
      label: "Chat",
      icon: MessageCircle,
      path: "/ai-assistant",
    },
    {
      id: "account",
      label: "Account",
      icon: User,
      path: user ? "/dashboard" : "/login",
    },
  ];

  const handleNavClick = (item: NavItem) => {
    // If requires auth and user not logged in, redirect to login (staff)
    if (item.requiresAuth && !user) {
      if (item.id === 'saved') {
        navigate("/properties"); // Saved doesn't exist for guests
        return;
      }
      navigate("/login", { state: { from: item.path } });
      return;
    }

    navigate(item.path);
  };

  const isActive = (path: string) => {
    // Special handling for home path
    if (path === "/properties") {
      return location.pathname === "/" || location.pathname === "/properties";
    }
    return location.pathname === path;
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-background border-t border-border md:hidden">
      <div className="flex items-center justify-around h-16 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);

          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item)}
              className={cn(
                "flex flex-col items-center justify-center flex-1 h-full gap-1 transition-colors relative",
                active
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
              aria-label={item.label}
              aria-current={active ? "page" : undefined}
            >
              <div className="relative">
                <Icon className={cn("h-5 w-5", active && "fill-primary/20")} />
                {item.badge && item.badge > 0 && (
                  <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] font-medium text-destructive-foreground">
                    {item.badge > 9 ? "9+" : item.badge}
                  </span>
                )}
              </div>
              <span
                className={cn(
                  "text-[10px] font-medium",
                  active && "font-semibold"
                )}
              >
                {item.label}
              </span>
              {active && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-0.5 bg-primary rounded-b-full" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
