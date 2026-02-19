/**
 * AppHeader Component
 * Mobile-first app header inspired by YouVersion Bible app
 */

import { ArrowLeft, Search, Bell, MoreVertical } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface AppHeaderProps {
  title?: string;
  subtitle?: string;
  showBack?: boolean;
  showSearch?: boolean;
  showNotifications?: boolean;
  showMenu?: boolean;
  transparent?: boolean;
  onBack?: () => void;
  onSearch?: () => void;
  onNotifications?: () => void;
  onMenu?: () => void;
  className?: string;
}

export function AppHeader({
  title,
  subtitle,
  showBack = false,
  showSearch = false,
  showNotifications = false,
  showMenu = false,
  transparent = false,
  onBack,
  onSearch,
  onNotifications,
  onMenu,
  className,
}: AppHeaderProps) {
  const navigate = useNavigate();

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate(-1);
    }
  };

  return (
    <header
      className={cn(
        'sticky top-0 z-50 transition-all',
        transparent
          ? 'bg-transparent'
          : 'bg-background/95 backdrop-blur-sm border-b border-border',
        className
      )}
    >
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-14">
          {/* Left Section */}
          <div className="flex items-center gap-2 flex-1 min-w-0">
            {showBack && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleBack}
                className="shrink-0"
              >
                <ArrowLeft className="w-5 h-5" />
              </Button>
            )}

            {/* Title Section */}
            {(title || subtitle) && (
              <div className="min-w-0">
                {title && (
                  <h1 
                    className={cn(
                      "font-serif text-xl font-bold text-foreground truncate",
                      title === "Fresh Manna" || title === "FreshManna" ? "cursor-pointer hover:text-secondary transition-colors" : ""
                    )}
                    onClick={() => {
                      if (title === "Fresh Manna" || title === "FreshManna") {
                        navigate('/');
                      }
                    }}
                  >
                    {title}
                  </h1>
                )}
                {subtitle && (
                  <p className="text-xs text-muted-foreground truncate">
                    {subtitle}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Right Section */}
          <div className="flex items-center gap-1 shrink-0">
            {showSearch && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onSearch}
                className="hover:bg-secondary/10"
              >
                <Search className="w-5 h-5" />
              </Button>
            )}

            {showNotifications && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onNotifications}
                className="hover:bg-secondary/10 relative"
              >
                <Bell className="w-5 h-5" />
                {/* Notification badge */}
                <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full" />
              </Button>
            )}

            {showMenu && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onMenu}
                className="hover:bg-secondary/10"
              >
                <MoreVertical className="w-5 h-5" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
