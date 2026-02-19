/**
 * Mobile Header Component
 *
 * Displays hamburger menu button and branding on mobile devices.
 * Only visible on screens < 1024px (lg breakpoint).
 */

import { Menu, Building2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface MobileHeaderProps {
  onMenuClick: () => void;
}

export function MobileHeader({ onMenuClick }: MobileHeaderProps) {
  return (
    <div className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 lg:hidden">
      <Button
        variant="ghost"
        size="icon"
        onClick={onMenuClick}
        className="h-10 w-10"
        aria-label="Toggle menu"
      >
        <Menu className="h-5 w-5" />
      </Button>

      <div className="flex items-center gap-2">
        <img src="/logo.png" alt="Diaserve Properties" className="h-12 w-auto" />
      </div>
    </div>
  );
}
