import { Container } from '@/components/ui/Container';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { Calendar, Users, MapPin, Award } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface Stat {
  icon: LucideIcon;
  value: string;
  label: string;
}

const stats: Stat[] = [
  { icon: Calendar, value: '25+', label: 'Years of Service' },
  { icon: Users, value: '100K+', label: 'Satisfied Clients' },
  { icon: MapPin, value: '30+', label: 'Branches Nationwide' },
  { icon: Award, value: '15+', label: 'Industry Awards' },
];

export function WhyChooseUs() {
  return (
    <section className="relative bg-navy py-20">
      {/* Decorative */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -right-32 -top-32 h-96 w-96 rounded-full bg-white/5" />
        <div className="absolute -bottom-16 -left-16 h-64 w-64 rounded-full bg-gold/10" />
      </div>

      <Container className="relative">
        <SectionHeader
          overline="Our Track Record"
          title="Why Choose StarLife?"
          dark
        />

        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div
                key={stat.label}
                className="group rounded-lg border border-white/10 bg-white/5 p-8 text-center backdrop-blur-sm transition-all duration-300 hover:border-gold/30 hover:bg-white/10"
              >
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gold/20">
                  <Icon className="h-7 w-7 text-gold" />
                </div>
                <p className="mb-1 text-4xl font-bold text-white">{stat.value}</p>
                <p className="text-sm text-white/60">{stat.label}</p>
              </div>
            );
          })}
        </div>
      </Container>
    </section>
  );
}
