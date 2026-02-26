import { useState } from 'react';
import { navigationItems } from '@/data/navigation';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MobileMenuProps {
  open: boolean;
  onClose: () => void;
}

export function MobileMenu({ open, onClose }: MobileMenuProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (!open) return null;

  const toggleExpanded = (label: string) => {
    setExpanded((prev) => (prev === label ? null : label));
  };

  return (
    <div className="animate-slide-down border-t border-gray-100 bg-white lg:hidden">
      <div className="space-y-1 px-4 py-3">
        {navigationItems.map((item) => (
          <div key={item.label}>
            {item.children ? (
              <>
                <button
                  onClick={() => toggleExpanded(item.label)}
                  className="flex w-full items-center justify-between rounded px-3 py-2.5 text-sm font-medium text-navy transition-colors hover:bg-navy/5"
                >
                  {item.label}
                  <ChevronDown
                    className={cn(
                      'h-4 w-4 transition-transform duration-200',
                      expanded === item.label && 'rotate-180',
                    )}
                  />
                </button>
                {expanded === item.label && (
                  <div className="ml-4 space-y-1 border-l-2 border-gold/30 pl-3">
                    {item.children.map((child) => (
                      <a
                        key={child.label}
                        href={child.href}
                        onClick={onClose}
                        className="block rounded px-3 py-2 text-sm text-gray-600 transition-colors hover:bg-navy/5 hover:text-navy"
                      >
                        {child.label}
                      </a>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <a
                href={item.href}
                onClick={onClose}
                className="block rounded px-3 py-2.5 text-sm font-medium text-navy transition-colors hover:bg-navy/5"
              >
                {item.label}
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
