export interface Slide {
  id: number;
  title: string;
  subtitle: string;
  description: string;
  cta: string;
  ctaHref: string;
  gradient: string;
}

export const slides: Slide[] = [
  {
    id: 1,
    title: 'Securing Your Future',
    subtitle: 'Life Insurance',
    description:
      'Protect your family with comprehensive life insurance plans tailored to your needs.',
    cta: 'Get a Quote',
    ctaHref: '#products',
    gradient: 'from-navy via-navy-light to-blue-accent',
  },
  {
    id: 2,
    title: 'Plan for Tomorrow',
    subtitle: 'Pension Plans',
    description:
      'Build a comfortable retirement with our flexible pension and savings plans.',
    cta: 'Learn More',
    ctaHref: '#products',
    gradient: 'from-navy-dark via-navy to-navy-light',
  },
  {
    id: 3,
    title: 'Invest in Education',
    subtitle: 'Education Policy',
    description:
      "Give your children the best start in life with our education savings plans.",
    cta: 'Start Saving',
    ctaHref: '#products',
    gradient: 'from-blue-accent via-navy-light to-navy',
  },
  {
    id: 4,
    title: 'Grow Your Wealth',
    subtitle: 'Investment Plans',
    description:
      'Maximize your returns with our diverse range of investment products.',
    cta: 'Explore Plans',
    ctaHref: '#products',
    gradient: 'from-navy via-blue-accent to-navy-light',
  },
  {
    id: 5,
    title: 'Group Life Assurance',
    subtitle: 'Corporate Solutions',
    description:
      'Comprehensive group life cover for your employees and organizations.',
    cta: 'Contact Us',
    ctaHref: '#contact',
    gradient: 'from-navy-dark via-navy to-blue-accent',
  },
  {
    id: 6,
    title: 'Peace of Mind',
    subtitle: 'Funeral Policy',
    description:
      'Affordable funeral plans that protect your family during difficult times.',
    cta: 'View Plans',
    ctaHref: '#products',
    gradient: 'from-navy-light via-navy to-navy-dark',
  },
];
