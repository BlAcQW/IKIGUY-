export interface NavItem {
  label: string;
  href: string;
  children?: NavItem[];
}

export const navigationItems: NavItem[] = [
  { label: 'Home', href: '#' },
  {
    label: 'About Us',
    href: '#about',
    children: [
      { label: 'Our Story', href: '#about' },
      { label: 'Board of Directors', href: '#about' },
      { label: 'Management Team', href: '#about' },
      { label: 'Corporate Governance', href: '#about' },
    ],
  },
  {
    label: 'Products',
    href: '#products',
    children: [
      { label: 'Individual Life', href: '#products' },
      { label: 'Group Life', href: '#products' },
      { label: 'Pension Plans', href: '#products' },
      { label: 'Investment Plans', href: '#products' },
      { label: 'Education Plans', href: '#products' },
      { label: 'Funeral Plans', href: '#products' },
    ],
  },
  {
    label: 'Media',
    href: '#news',
    children: [
      { label: 'News & Events', href: '#news' },
      { label: 'Gallery', href: '#news' },
      { label: 'Downloads', href: '#news' },
    ],
  },
  {
    label: 'Careers',
    href: '#careers',
    children: [
      { label: 'Current Openings', href: '#careers' },
      { label: 'Life at StarLife', href: '#careers' },
    ],
  },
  { label: 'Contact', href: '#contact' },
];

export const topBarLinks = [
  { label: 'Web Portal', href: '#' },
  { label: 'Get Insurance', href: '#' },
  { label: 'Online Payment', href: '#' },
];
