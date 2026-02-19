import {
  LayoutDashboard,
  Building2,
  Users,
  Calendar,
  FileText,
  MessageSquare,
  Phone,
  Mail,
  Sparkles,
  Settings,
  HelpCircle,
  Search,
  ChevronDown,
  Megaphone,
  CreditCard,
  LogOut,
  Shield
} from "lucide-react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent } from "@/components/ui/sheet";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Properties", href: "/properties", icon: Building2 },
  { name: "Contacts", href: "/contacts", icon: Users },
  { name: "Bookings", href: "/bookings", icon: Calendar },
  { name: "Campaigns", href: "/campaigns", icon: Megaphone },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Invoices", href: "/invoices", icon: CreditCard },
];

const aiTools = [
  { name: "AI Chat", href: "/ai-chat", icon: MessageSquare },
  { name: "Voice Agent", href: "/voice-agent", icon: Phone },
  { name: "AI Assistant", href: "/ai-assistant", icon: Sparkles },
];

const bottomNav = [
  { name: "Settings", href: "/settings", icon: Settings },
  { name: "Help", href: "/help", icon: HelpCircle },
];

const adminNav = [
  { name: "Admin Panel", href: "/admin", icon: Shield },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  isMobile?: boolean;
}

export function Sidebar({ isOpen = false, onClose, isMobile = false }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();

  // Check if user is admin
  const isAdmin = user?.role === 'admin' || user?.email === 'admin@ailabsafrica.com' || user?.email === 'admin@estateflow.local';

  const handleSignOut = async () => {
    await signOut();
    navigate("/login");
  };

  const getUserInitials = () => {
    if (!user?.email) return "U";
    const email = user.email;
    const parts = email.split("@")[0].split(".");
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return email.substring(0, 2).toUpperCase();
  };

  const handleNavClick = () => {
    if (isMobile && onClose) {
      onClose();
    }
  };

  const sidebarContent = (
    <>
      <div className="flex h-24 items-center px-6 border-b border-sidebar-border">
        <img src="/logo.png" alt="Diaserve Properties" className="h-20 w-auto" />
      </div>

      <div className="h-4" /> {/* Spacer */}

      {/* Search */}
      <div className="px-4 pb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-sidebar-foreground/50" />
          <input
            type="text"
            placeholder="Search..."
            className="w-full rounded-lg bg-sidebar-accent border-0 py-2 pl-9 pr-4 text-sm text-sidebar-foreground placeholder:text-sidebar-foreground/50 focus:outline-none focus:ring-2 focus:ring-sidebar-ring"
          />
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 space-y-1 px-3 overflow-y-auto">
        <div className="mb-2">
          <span className="px-3 text-xs font-medium uppercase tracking-wider text-sidebar-foreground/50">
            Main
          </span>
        </div>
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <NavLink
              key={item.name}
              to={item.href}
              onClick={handleNavClick}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-sidebar-primary text-sidebar-primary-foreground"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-foreground"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </NavLink>
          );
        })}

        {/* AI Tools Section */}
        <div className="mt-6 mb-2">
          <span className="px-3 text-xs font-medium uppercase tracking-wider text-sidebar-foreground/50">
            AI Tools
          </span>
        </div>
        {aiTools.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <NavLink
              key={item.name}
              to={item.href}
              onClick={handleNavClick}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-sidebar-primary text-sidebar-primary-foreground"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-foreground"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
              {item.name === "AI Chat" && (
                <span className="ml-auto flex h-5 items-center rounded-full bg-sidebar-primary/20 px-2 text-xs text-sidebar-primary">
                  New
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Navigation */}
      <div className="border-t border-sidebar-border p-3 space-y-1">
        {/* Admin Panel (only for admin users) */}
        {isAdmin && adminNav.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <NavLink
              key={item.name}
              to={item.href}
              onClick={handleNavClick}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-gradient-to-r from-accent to-warning text-foreground shadow-glow"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-foreground"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </NavLink>
          );
        })}

        {/* Regular bottom nav */}
        {bottomNav.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            onClick={handleNavClick}
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-foreground transition-all duration-200"
          >
            <item.icon className="h-5 w-5" />
            {item.name}
          </NavLink>
        ))}
      </div>

      {/* User Profile */}
      <div className="border-t border-sidebar-border p-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex w-full items-center gap-3 rounded-lg p-2 hover:bg-sidebar-accent transition-colors">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-accent to-orange-600 text-white text-sm font-semibold">
                {getUserInitials()}
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-medium text-sidebar-foreground truncate">
                  {user?.email?.split("@")[0] || "User"}
                </p>
                <p className="text-xs text-sidebar-foreground/60">
                  {user?.email || "No email"}
                </p>
              </div>
              <ChevronDown className="h-4 w-4 text-sidebar-foreground/50" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate("/settings")}>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleSignOut}>
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </>
  );

  // Desktop: Fixed sidebar
  if (!isMobile) {
    return (
      <aside className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-50 lg:flex lg:w-64 lg:flex-col bg-sidebar border-r border-sidebar-border">
        {sidebarContent}
      </aside>
    );
  }

  // Mobile: Sheet drawer
  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent side="left" className="w-64 p-0 bg-sidebar border-sidebar-border flex flex-col">
        {sidebarContent}
      </SheetContent>
    </Sheet>
  );
}
