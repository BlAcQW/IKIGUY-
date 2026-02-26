import type { LucideIcon } from 'lucide-react';
import { Shield, GraduationCap, PiggyBank, Users, Heart, Landmark } from 'lucide-react';

export interface Product {
  id: number;
  title: string;
  description: string;
  icon: LucideIcon;
  gradient: string;
}

export const products: Product[] = [
  {
    id: 1,
    title: 'Individual Life Insurance',
    description:
      'Comprehensive life cover that protects you and your loved ones with flexible premium options.',
    icon: Shield,
    gradient: 'from-navy to-navy-light',
  },
  {
    id: 2,
    title: 'Education Policy',
    description:
      "Secure your children's future with savings plans designed to fund their education at every level.",
    icon: GraduationCap,
    gradient: 'from-blue-accent to-navy-light',
  },
  {
    id: 3,
    title: 'Pension Plans',
    description:
      'Build a solid retirement fund with our range of pension products offering competitive returns.',
    icon: PiggyBank,
    gradient: 'from-navy-light to-navy',
  },
  {
    id: 4,
    title: 'Group Life Assurance',
    description:
      'Protect your employees with affordable group life cover tailored for businesses of all sizes.',
    icon: Users,
    gradient: 'from-navy to-blue-accent',
  },
  {
    id: 5,
    title: 'Funeral Policy',
    description:
      'Affordable funeral plans that provide financial support to your family when they need it most.',
    icon: Heart,
    gradient: 'from-navy-dark to-navy',
  },
  {
    id: 6,
    title: 'Investment Plans',
    description:
      'Grow your wealth with our professionally managed investment products and savings schemes.',
    icon: Landmark,
    gradient: 'from-navy-light to-blue-accent',
  },
];
