import { Container } from '@/components/ui/Container';
import { topBarLinks } from '@/data/navigation';
import { Phone, Mail } from 'lucide-react';

export function TopBar() {
  return (
    <div className="bg-navy-dark py-2 text-xs text-white/80">
      <Container className="flex items-center justify-between">
        <div className="hidden items-center gap-4 sm:flex">
          <span className="flex items-center gap-1">
            <Phone className="h-3 w-3" />
            +233 302 123 456
          </span>
          <span className="flex items-center gap-1">
            <Mail className="h-3 w-3" />
            info@starlife.com.gh
          </span>
        </div>
        <div className="flex items-center gap-3 sm:gap-4">
          {topBarLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="rounded bg-gold/90 px-3 py-1 text-xs font-semibold text-navy-dark transition-colors hover:bg-gold"
            >
              {link.label}
            </a>
          ))}
        </div>
      </Container>
    </div>
  );
}
