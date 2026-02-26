import { Container } from '@/components/ui/Container';
import { Button } from '@/components/ui/Button';
import { CheckCircle, Building2 } from 'lucide-react';

const features = [
  'Over 25 years of trusted service in Ghana',
  'Regulated by the National Insurance Commission',
  'Wide range of life insurance and pension products',
  'Dedicated claims processing and customer support',
];

export function AboutSection() {
  return (
    <section id="about" className="bg-white py-20">
      <Container>
        <div className="grid items-center gap-12 lg:grid-cols-2">
          {/* Gradient Placeholder Image */}
          <div className="relative">
            <div className="aspect-[4/3] overflow-hidden rounded-lg bg-gradient-to-br from-navy via-navy-light to-blue-accent">
              <div className="flex h-full items-center justify-center">
                <Building2 className="h-24 w-24 text-white/20" />
              </div>
              {/* Decorative overlay */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-navy/60 to-transparent p-6">
                <p className="text-sm font-semibold text-gold">Est. 1998</p>
                <p className="text-lg font-bold text-white">StarLife Head Office, Accra</p>
              </div>
            </div>
            {/* Accent block */}
            <div className="absolute -bottom-4 -right-4 -z-10 h-full w-full rounded-lg bg-gold/20" />
          </div>

          {/* Text Content */}
          <div>
            <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-gold">
              About StarLife
            </p>
            <h2 className="mb-4 text-3xl font-bold text-navy md:text-4xl">
              Your Trusted Partner in Life Insurance
            </h2>
            <p className="mb-6 leading-relaxed text-gray-600">
              StarLife Assurance Company Limited is one of Ghana's leading life insurance
              companies. We are committed to providing innovative and affordable insurance
              solutions that help individuals, families, and businesses protect their
              financial futures.
            </p>
            <p className="mb-8 leading-relaxed text-gray-600">
              With a strong network of branches across Ghana and a team of experienced
              professionals, we deliver personalized service and reliable coverage you can
              count on.
            </p>

            <ul className="mb-8 space-y-3">
              {features.map((feat) => (
                <li key={feat} className="flex items-start gap-3">
                  <CheckCircle className="mt-0.5 h-5 w-5 shrink-0 text-gold" />
                  <span className="text-sm text-gray-700">{feat}</span>
                </li>
              ))}
            </ul>

            <Button variant="gold">Discover More</Button>
          </div>
        </div>
      </Container>
    </section>
  );
}
