import { useState, useCallback } from 'react';
import { useInterval } from '@/hooks/useInterval';
import { slides } from '@/data/slides';
import { Container } from '@/components/ui/Container';
import { Button } from '@/components/ui/Button';
import { ChevronLeft, ChevronRight, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';

export function HeroCarousel() {
  const [current, setCurrent] = useState(0);
  const [paused, setPaused] = useState(false);

  const next = useCallback(() => {
    setCurrent((prev) => (prev + 1) % slides.length);
  }, []);

  const prev = useCallback(() => {
    setCurrent((prev) => (prev - 1 + slides.length) % slides.length);
  }, []);

  const goTo = useCallback((index: number) => {
    setCurrent(index);
    setPaused(true);
    setTimeout(() => setPaused(false), 8000);
  }, []);

  useInterval(next, paused ? null : 5000);

  return (
    <section
      className="relative overflow-hidden"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {/* Slides */}
      <div className="relative h-[520px] md:h-[600px]">
        {slides.map((slide, i) => (
          <div
            key={slide.id}
            className={cn(
              'absolute inset-0 bg-gradient-to-br transition-opacity duration-700',
              slide.gradient,
              i === current ? 'opacity-100' : 'opacity-0',
            )}
          >
            {/* Decorative elements */}
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute -right-20 -top-20 h-96 w-96 rounded-full bg-white/5" />
              <div className="absolute -bottom-10 -left-10 h-72 w-72 rounded-full bg-white/5" />
              <div className="absolute right-1/4 top-1/3 h-48 w-48 rounded-full bg-gold/10" />
            </div>

            <Container className="relative flex h-full items-center">
              <div
                className={cn(
                  'max-w-xl transition-all duration-700',
                  i === current
                    ? 'translate-y-0 opacity-100'
                    : 'translate-y-8 opacity-0',
                )}
              >
                <div className="mb-3 flex items-center gap-2">
                  <Shield className="h-5 w-5 text-gold" />
                  <span className="text-sm font-semibold uppercase tracking-widest text-gold">
                    {slide.subtitle}
                  </span>
                </div>
                <h1 className="mb-4 text-4xl font-bold leading-tight text-white md:text-5xl lg:text-6xl">
                  {slide.title}
                </h1>
                <p className="mb-8 text-lg text-white/80">{slide.description}</p>
                <div className="flex gap-4">
                  <Button variant="gold">
                    <a href={slide.ctaHref}>{slide.cta}</a>
                  </Button>
                  <Button variant="outline">Learn More</Button>
                </div>
              </div>
            </Container>
          </div>
        ))}
      </div>

      {/* Arrows */}
      <button
        onClick={() => {
          prev();
          setPaused(true);
          setTimeout(() => setPaused(false), 8000);
        }}
        className="absolute left-4 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/20 text-white backdrop-blur-sm transition-colors hover:bg-white/30"
        aria-label="Previous slide"
      >
        <ChevronLeft className="h-5 w-5" />
      </button>
      <button
        onClick={() => {
          next();
          setPaused(true);
          setTimeout(() => setPaused(false), 8000);
        }}
        className="absolute right-4 top-1/2 z-10 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-white/20 text-white backdrop-blur-sm transition-colors hover:bg-white/30"
        aria-label="Next slide"
      >
        <ChevronRight className="h-5 w-5" />
      </button>

      {/* Dots */}
      <div className="absolute bottom-6 left-1/2 z-10 flex -translate-x-1/2 gap-2">
        {slides.map((_, i) => (
          <button
            key={i}
            onClick={() => goTo(i)}
            className={cn(
              'h-2.5 rounded-full transition-all duration-300',
              i === current ? 'w-8 bg-gold' : 'w-2.5 bg-white/50 hover:bg-white/70',
            )}
            aria-label={`Go to slide ${i + 1}`}
          />
        ))}
      </div>
    </section>
  );
}
