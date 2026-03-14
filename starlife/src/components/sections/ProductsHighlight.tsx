import { Container } from '@/components/ui/Container';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { products } from '@/data/products';
import { ArrowRight } from 'lucide-react';

export function ProductsHighlight() {
  return (
    <section id="products" className="bg-light-bg py-20">
      <Container>
        <SectionHeader overline="What We Offer" title="Our Products" />

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => {
            const Icon = product.icon;
            return (
              <div
                key={product.id}
                className="group rounded-lg bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
              >
                <div
                  className={`mb-4 flex h-14 w-14 items-center justify-center rounded-lg bg-gradient-to-br ${product.gradient}`}
                >
                  <Icon className="h-7 w-7 text-white" />
                </div>
                <h3 className="mb-2 text-lg font-bold text-navy">{product.title}</h3>
                <p className="mb-4 text-sm leading-relaxed text-gray-600">
                  {product.description}
                </p>
                <a
                  href="#"
                  className="inline-flex items-center gap-1 text-sm font-semibold text-gold transition-colors hover:text-gold-light"
                >
                  Learn More
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </a>
              </div>
            );
          })}
        </div>
      </Container>
    </section>
  );
}
