import { Container } from '@/components/ui/Container';
import { footerColumns, socialLinks } from '@/data/footer';
import { Star, Facebook, Twitter, Linkedin, Instagram } from 'lucide-react';

const socialIcons: Record<string, typeof Facebook> = {
  Facebook,
  Twitter,
  LinkedIn: Linkedin,
  Instagram,
};

export function Footer() {
  return (
    <footer className="bg-navy-dark text-white/80">
      <Container className="py-16">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-5">
          {/* Brand Column */}
          <div className="lg:col-span-1">
            <a href="#" className="mb-4 flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded bg-gold">
                <Star className="h-5 w-5 text-navy-dark" fill="currentColor" />
              </div>
              <div className="leading-tight">
                <span className="text-base font-bold text-white">StarLife</span>
                <span className="block text-[9px] font-medium uppercase tracking-widest text-gold">
                  Assurance
                </span>
              </div>
            </a>
            <p className="mt-4 text-sm leading-relaxed text-white/60">
              Providing quality life insurance, pension, and investment products to
              Ghanaians for over 25 years.
            </p>
            <div className="mt-6 flex gap-3">
              {socialLinks.map((link) => {
                const Icon = socialIcons[link.label] ?? Facebook;
                return (
                  <a
                    key={link.label}
                    href={link.href}
                    className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 transition-colors hover:bg-gold hover:text-navy-dark"
                    aria-label={link.label}
                  >
                    <Icon className="h-4 w-4" />
                  </a>
                );
              })}
            </div>
          </div>

          {/* Link Columns */}
          {footerColumns.map((col) => (
            <div key={col.title}>
              <h4 className="mb-4 text-sm font-bold uppercase tracking-wider text-white">
                {col.title}
              </h4>
              <ul className="space-y-2.5">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm text-white/60 transition-colors hover:text-gold"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Container>

      {/* Bottom Bar */}
      <div className="border-t border-white/10">
        <Container className="flex flex-col items-center justify-between gap-3 py-5 text-xs text-white/40 sm:flex-row">
          <p>&copy; {new Date().getFullYear()} StarLife Assurance. All rights reserved.</p>
          <div className="flex gap-4">
            <a href="#" className="transition-colors hover:text-gold">
              Privacy Policy
            </a>
            <a href="#" className="transition-colors hover:text-gold">
              Terms of Service
            </a>
            <a href="#" className="transition-colors hover:text-gold">
              Sitemap
            </a>
          </div>
        </Container>
      </div>
    </footer>
  );
}
