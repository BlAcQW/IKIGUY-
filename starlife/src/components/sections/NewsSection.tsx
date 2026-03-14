import { Container } from '@/components/ui/Container';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { Calendar, ArrowRight, Newspaper } from 'lucide-react';

interface NewsItem {
  id: number;
  title: string;
  excerpt: string;
  date: string;
  category: string;
  gradient: string;
}

const newsItems: NewsItem[] = [
  {
    id: 1,
    title: 'StarLife Launches New Education Savings Plan',
    excerpt:
      "Our new FlexiEdu plan offers parents flexible savings options for their children's education.",
    date: 'Feb 15, 2026',
    category: 'Products',
    gradient: 'from-navy to-navy-light',
  },
  {
    id: 2,
    title: 'Annual General Meeting Highlights',
    excerpt:
      'StarLife reports strong growth and announces plans for branch expansion across Ghana.',
    date: 'Feb 8, 2026',
    category: 'Corporate',
    gradient: 'from-blue-accent to-navy-light',
  },
  {
    id: 3,
    title: 'Community Health Outreach Program',
    excerpt:
      'StarLife partners with local communities to provide free health screenings and wellness education.',
    date: 'Jan 28, 2026',
    category: 'CSR',
    gradient: 'from-navy-light to-navy',
  },
  {
    id: 4,
    title: 'Digital Transformation: New Customer Portal',
    excerpt:
      'Manage your policies, make payments, and file claims online with our new self-service portal.',
    date: 'Jan 15, 2026',
    category: 'Technology',
    gradient: 'from-navy to-blue-accent',
  },
];

export function NewsSection() {
  return (
    <section id="news" className="bg-light-bg py-20">
      <Container>
        <SectionHeader overline="Stay Updated" title="Latest News & Events" />

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {newsItems.map((item) => (
            <article
              key={item.id}
              className="group overflow-hidden rounded-lg bg-white shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg"
            >
              {/* Gradient image placeholder */}
              <div
                className={`relative h-44 bg-gradient-to-br ${item.gradient}`}
              >
                <div className="flex h-full items-center justify-center">
                  <Newspaper className="h-12 w-12 text-white/20" />
                </div>
                <span className="absolute left-3 top-3 rounded bg-gold px-2 py-1 text-xs font-semibold text-navy-dark">
                  {item.category}
                </span>
              </div>

              <div className="p-5">
                <div className="mb-2 flex items-center gap-1.5 text-xs text-gray-400">
                  <Calendar className="h-3.5 w-3.5" />
                  {item.date}
                </div>
                <h3 className="mb-2 text-sm font-bold leading-snug text-navy line-clamp-2">
                  {item.title}
                </h3>
                <p className="mb-3 text-xs leading-relaxed text-gray-500 line-clamp-2">
                  {item.excerpt}
                </p>
                <a
                  href="#"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-gold transition-colors hover:text-gold-light"
                >
                  Read More
                  <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
                </a>
              </div>
            </article>
          ))}
        </div>
      </Container>
    </section>
  );
}
