import { useState } from 'react';
import { Container } from '@/components/ui/Container';
import { navigationItems } from '@/data/navigation';
import { MobileMenu } from './MobileMenu';
import { Menu, X, Star, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 bg-white shadow-md">
      <Container className="flex items-center justify-between py-3">
        {/* Logo */}
        <a href="#" className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded bg-navy">
            <Star className="h-6 w-6 text-gold" fill="currentColor" />
          </div>
          <div className="leading-tight">
            <span className="text-lg font-bold text-navy">StarLife</span>
            <span className="block text-[10px] font-medium uppercase tracking-widest text-gray-500">
              Assurance
            </span>
          </div>
        </a>

        {/* Desktop Nav */}
        <div className="hidden items-center gap-1 lg:flex">
          {navigationItems.map((item) => (
            <div key={item.label} className="group relative">
              <a
                href={item.href}
                className="flex items-center gap-1 rounded px-3 py-2 text-sm font-medium text-navy transition-colors hover:bg-navy/5 hover:text-navy-light"
              >
                {item.label}
                {item.children && <ChevronDown className="h-3.5 w-3.5" />}
              </a>

              {/* Dropdown */}
              {item.children && (
                <div className="invisible absolute left-0 top-full z-50 min-w-[200px] rounded-md bg-white py-2 opacity-0 shadow-lg transition-all duration-200 group-hover:visible group-hover:opacity-100">
                  {item.children.map((child) => (
                    <a
                      key={child.label}
                      href={child.href}
                      className="block px-4 py-2 text-sm text-gray-700 transition-colors hover:bg-navy/5 hover:text-navy"
                    >
                      {child.label}
                    </a>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Mobile Toggle */}
        <button
          onClick={() => setMobileOpen((prev) => !prev)}
          className={cn(
            'rounded p-2 text-navy transition-colors hover:bg-navy/5 lg:hidden',
          )}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </Container>

      {/* Mobile Menu */}
      <MobileMenu open={mobileOpen} onClose={() => setMobileOpen(false)} />
    </nav>
  );
}
