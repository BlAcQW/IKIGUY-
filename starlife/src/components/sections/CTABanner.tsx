import { Container } from '@/components/ui/Container';
import { Button } from '@/components/ui/Button';

export function CTABanner() {
  return (
    <section className="bg-gradient-to-r from-gold via-gold-light to-gold py-16">
      <Container className="text-center">
        <h2 className="mb-4 text-3xl font-bold text-navy-dark md:text-4xl">
          Ready to Secure Your Future?
        </h2>
        <p className="mx-auto mb-8 max-w-2xl text-navy-dark/80">
          Get in touch with our team today and find the perfect insurance plan for you
          and your family. Your peace of mind is our priority.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <Button variant="blue">Get a Free Quote</Button>
          <Button
            className="border-2 border-navy-dark bg-transparent text-navy-dark hover:bg-navy-dark hover:text-white"
          >
            Contact an Agent
          </Button>
        </div>
      </Container>
    </section>
  );
}
