import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useAccessibility } from '@/components/AccessibilityProvider';
import {
  Menu,
  X,
  User,
  LogOut,
  Settings,
  Wallet,
  Home,
  FileText,
  MessageSquare,
  Calendar,
  Plus,
  ChevronRight,
  Briefcase
} from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Separator } from '@/components/ui/separator';
import ImageOptimizer from '@/components/ImageOptimizer';
import ThemeToggle from '@/components/ThemeToggle';

interface MobileNavigationProps {
  className?: string;
}

const MobileNavigation: React.FC<MobileNavigationProps> = ({ className }) => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const { announceToScreenReader } = useAccessibility();

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
    setIsOpen(false);
    announceToScreenReader('Signed out successfully');
  };

  const isActive = (path: string) => location.pathname === path;

  const navigationItems = [
    { path: '/', label: 'Home', icon: Home },
    { path: '/demos', label: 'Demos', icon: FileText },
    { path: '/contact', label: 'Contact', icon: MessageSquare },
    { path: '/careers', label: 'Careers', icon: Briefcase },
    { path: '/schedule-demo', label: 'Schedule Demo', icon: Calendar },
    { path: '/create-assistant', label: 'Create Assistant', icon: Plus },
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
    setIsOpen(false);
  };

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          aria-label="Open mobile menu"
        >
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[300px] sm:w-[400px] p-0">
        <SheetHeader className="p-4 border-b">
          <SheetTitle className="flex items-center space-x-2">
            <ImageOptimizer
              src="/lovable-uploads/b1d3a13a-9e6f-4719-b67a-6132a9b191b3.png"
              alt="AI Labs Africa logo"
              className="h-6 w-6"
              width={24}
              height={24}
              priority={true}
              loading="eager"
            />
            <span className="font-bold text-lg gradient-text">
              AI Labs Africa
            </span>
          </SheetTitle>
        </SheetHeader>

        <div className="flex flex-col h-full">
          {/* Main Navigation */}
          <div className="flex-1 p-4">
            <nav className="space-y-2">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Button
                    key={item.path}
                    variant={isActive(item.path) ? "secondary" : "ghost"}
                    className="w-full justify-start h-12 px-4"
                    onClick={() => handleNavigation(item.path)}
                    aria-current={isActive(item.path) ? 'page' : undefined}
                  >
                    <Icon className="h-4 w-4 mr-3" />
                    <span className="text-sm font-medium">{item.label}</span>
                    {isActive(item.path) && (
                      <ChevronRight className="h-4 w-4 ml-auto" />
                    )}
                  </Button>
                );
              })}
            </nav>

            <Separator className="my-4" />

            {/* Theme Toggle */}
            <div className="flex items-center justify-between p-2">
              <span className="text-sm font-medium">Theme</span>
              <ThemeToggle variant="outline" size="sm" />
            </div>
          </div>

          {/* User Section */}
          <div className="border-t p-4">
            {user ? (
              <div className="space-y-3">
                <div className="flex items-center space-x-3 p-3 bg-muted/50 rounded-lg">
                  <div className="h-8 w-8 bg-primary/10 rounded-full flex items-center justify-center">
                    <User className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {user.email?.split('@')[0]}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {user.email}
                    </p>
                  </div>
                </div>

                <div className="space-y-1">
                  <Button
                    variant="ghost"
                    className="w-full justify-start h-10 px-3"
                    onClick={() => handleNavigation('/dashboard')}
                  >
                    <Settings className="h-4 w-4 mr-3" />
                    <span className="text-sm">Dashboard</span>
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full justify-start h-10 px-3"
                    onClick={() => handleNavigation('/wallet')}
                  >
                    <Wallet className="h-4 w-4 mr-3" />
                    <span className="text-sm">Wallet</span>
                  </Button>
                  <Button
                    variant="ghost"
                    className="w-full justify-start h-10 px-3"
                    onClick={() => handleNavigation('/guest-access')}
                  >
                    <User className="h-4 w-4 mr-3" />
                    <span className="text-sm">Guest Access</span>
                  </Button>
                </div>

                <Separator />

                <Button
                  variant="ghost"
                  className="w-full justify-start h-10 px-3 text-destructive hover:text-destructive"
                  onClick={handleSignOut}
                >
                  <LogOut className="h-4 w-4 mr-3" />
                  <span className="text-sm">Sign Out</span>
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full h-10"
                  onClick={() => handleNavigation('/guest-dashboard')}
                >
                  <User className="h-4 w-4 mr-2" />
                  Guest Access
                </Button>
                <Button
                  variant="default"
                  className="w-full h-10"
                  onClick={() => handleNavigation('/auth')}
                >
                  Sign In
                </Button>
              </div>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default MobileNavigation;
