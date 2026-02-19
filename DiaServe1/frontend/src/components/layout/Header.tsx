import { Bell, Plus, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { OfflineIndicatorHeader } from "@/components/OfflineIndicator";

interface HeaderProps {
  title: string;
  subtitle?: string;
  showSearch?: boolean;
  actions?: React.ReactNode;
}

export function Header({ title, subtitle, showSearch = true, actions }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 flex h-14 md:h-16 items-center justify-between border-b border-border bg-background/80 backdrop-blur-xl px-4 md:px-6">
      <div className="flex items-center gap-2 md:gap-4 flex-1 min-w-0">
        <div className="min-w-0 flex-1 lg:flex-none">
          <h1 className="text-base md:text-xl font-semibold text-foreground truncate">{title}</h1>
          {subtitle && <p className="hidden sm:block text-xs md:text-sm text-muted-foreground truncate">{subtitle}</p>}
        </div>
      </div>

      <div className="flex items-center gap-2 md:gap-4">
        {showSearch && (
          <>
            {/* Desktop search bar */}
            <div className="relative hidden lg:block">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search properties, contacts..."
                className="w-64 xl:w-80 pl-9 bg-secondary border-0"
              />
            </div>

            {/* Mobile search icon */}
            <Button variant="ghost" size="icon" className="lg:hidden h-9 w-9">
              <Search className="h-4 w-4" />
            </Button>
          </>
        )}

        {/* Offline indicator for desktop */}
        <OfflineIndicatorHeader />

        {/* Actions with responsive sizing */}
        <div className="hidden sm:flex items-center gap-2">
          {actions}
        </div>

        {/* Notification bell with responsive sizing */}
        <Button variant="ghost" size="icon" className="relative h-9 w-9 md:h-10 md:w-10">
          <Bell className="h-4 w-4 md:h-5 md:w-5" />
          <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-accent text-[10px] font-bold text-accent-foreground">
            3
          </span>
        </Button>
      </div>
    </header>
  );
}
