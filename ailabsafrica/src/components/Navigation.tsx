import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useAccessibility } from '@/components/AccessibilityProvider';
import { User, LogOut, Settings, Wallet, CreditCard, Users, Share2, Globe, HelpCircle } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import ImageOptimizer from '@/components/ImageOptimizer';
import ThemeToggle from '@/components/ThemeToggle';
import KeyboardShortcutsHelp from '@/components/KeyboardShortcutsHelp';
import MobileNavigation from '@/components/MobileNavigation';
// import LanguageSwitcher from '@/components/LanguageSwitcher';
import { useHelp } from '@/contexts/HelpContext';

const Navigation = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const { announceToScreenReader } = useAccessibility();
  const { showHelpSection } = useHelp();

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
    announceToScreenReader('Signed out successfully');
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav 
      className="nav-blur sticky top-0 z-50 w-full border-b border-border/40 theme-transition"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-4">
          <MobileNavigation />
          <Link
            to="/"
            className="flex items-center space-x-2"
            aria-label="Go to home page"
          >
            <ImageOptimizer
              src="/lovable-uploads/b1d3a13a-9e6f-4719-b67a-6132a9b191b3.png"
              alt="AI Labs Africa logo"
              className="h-8 w-8"
              width={32}
              height={32}
              priority={true}
              loading="eager"
            />
            <span className="font-bold text-xl gradient-text">
              AI Labs Africa
            </span>
          </Link>
        </div>

        <div className="hidden xl:flex items-center space-x-6" role="menubar">
          <Link 
            to="/" 
            className={`text-sm font-medium transition-colors hover:text-primary ${
              isActive('/') ? 'text-primary' : 'text-muted-foreground'
            }`}
            role="menuitem"
            aria-current={isActive('/') ? 'page' : undefined}
            aria-label="Go to home page"
          >
            Home
          </Link>
          <Link 
            to="/demos" 
            className={`text-sm font-medium transition-colors hover:text-primary ${
              isActive('/demos') ? 'text-primary' : 'text-muted-foreground'
            }`}
            role="menuitem"
            aria-current={isActive('/demos') ? 'page' : undefined}
            aria-label="View demo pages"
          >
            Demos
          </Link>
          <Link 
            to="/faq" 
            className={`text-sm font-medium transition-colors hover:text-primary ${
              isActive('/faq') ? 'text-primary' : 'text-muted-foreground'
            }`}
            role="menuitem"
            aria-current={isActive('/faq') ? 'page' : undefined}
            aria-label="Frequently asked questions"
          >
            FAQ
          </Link>
          <Link
            to="/contact"
            className={`text-sm font-medium transition-colors hover:text-primary ${
              isActive('/contact') ? 'text-primary' : 'text-muted-foreground'
            }`}
            role="menuitem"
            aria-current={isActive('/contact') ? 'page' : undefined}
            aria-label="Contact us"
          >
            Contact
          </Link>
          <Link
            to="/careers"
            className={`text-sm font-medium transition-colors hover:text-primary ${
              isActive('/careers') || isActive('/recruitment') ? 'text-primary' : 'text-muted-foreground'
            }`}
            role="menuitem"
            aria-current={isActive('/careers') || isActive('/recruitment') ? 'page' : undefined}
            aria-label="Join our team"
          >
            Careers
          </Link>
          <Link
            to="/schedule-demo"
            className={`text-sm font-medium transition-colors hover:text-primary ${
              isActive('/schedule-demo') ? 'text-primary' : 'text-muted-foreground'
            }`}
            role="menuitem"
            aria-current={isActive('/schedule-demo') ? 'page' : undefined}
            aria-label="Schedule a demo call"
          >
            Schedule Demo
          </Link>
          {/* Hidden: Create Assistant, Theme Toggle, Help, Sign In - accessible via mobile menu only */}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
