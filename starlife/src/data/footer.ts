export interface FooterColumn {
  title: string;
  links: { label: string; href: string }[];
}

export const footerColumns: FooterColumn[] = [
  {
    title: 'Products',
    links: [
      { label: 'Individual Life', href: '#' },
      { label: 'Group Life', href: '#' },
      { label: 'Pension Plans', href: '#' },
      { label: 'Education Plans', href: '#' },
      { label: 'Investment Plans', href: '#' },
      { label: 'Funeral Plans', href: '#' },
    ],
  },
  {
    title: 'Company',
    links: [
      { label: 'About Us', href: '#' },
      { label: 'Board of Directors', href: '#' },
      { label: 'Management Team', href: '#' },
      { label: 'Careers', href: '#' },
      { label: 'Corporate Governance', href: '#' },
    ],
  },
  {
    title: 'Resources',
    links: [
      { label: 'News & Events', href: '#' },
      { label: 'Downloads', href: '#' },
      { label: 'Claims Process', href: '#' },
      { label: 'FAQs', href: '#' },
      { label: 'Gallery', href: '#' },
    ],
  },
  {
    title: 'Contact',
    links: [
      { label: 'Head Office: Accra', href: '#' },
      { label: 'Phone: +233 302 123 456', href: 'tel:+233302123456' },
      { label: 'Email: info@starlife.com.gh', href: 'mailto:info@starlife.com.gh' },
      { label: 'P.O. Box GP 851, Accra', href: '#' },
    ],
  },
];

export const socialLinks = [
  { label: 'Facebook', href: '#' },
  { label: 'Twitter', href: '#' },
  { label: 'LinkedIn', href: '#' },
  { label: 'Instagram', href: '#' },
];
