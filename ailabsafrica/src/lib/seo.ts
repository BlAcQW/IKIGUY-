/**
 * SEO Utilities and Helpers
 * Provides common SEO functions and configurations for the AI Labs Africa platform
 */

export interface SEOConfig {
  title: string;
  description: string;
  keywords?: string[];
  canonical?: string;
  ogImage?: string;
  ogType?: string;
  twitterCard?: string;
  noIndex?: boolean;
  noFollow?: boolean;
  language?: string;
  alternateLanguages?: Array<{
    language: string;
    url: string;
  }>;
}

export interface StructuredData {
  '@context': string;
  '@type': string;
  [key: string]: any;
}

export interface PageSEOData {
  path: string;
  title: string;
  description: string;
  keywords: string[];
  lastModified: string;
  changeFrequency: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never';
  priority: number;
  language: string;
}

// Default SEO configuration
export const DEFAULT_SEO_CONFIG: SEOConfig = {
  title: 'AI Labs Africa - AI Assistant Management Platform',
  description: 'Build, deploy, and manage AI assistants for African businesses. Voice AI, chatbots, and automation solutions.',
  keywords: ['AI', 'artificial intelligence', 'voice AI', 'chatbots', 'automation', 'Africa', 'business'],
  ogType: 'website',
  twitterCard: 'summary_large_image',
  language: 'en'
};

// Language-specific SEO configurations
export const LANGUAGE_SEO_CONFIGS: Record<string, Partial<SEOConfig>> = {
  en: {
    title: 'AI Labs Africa - AI Assistant Management Platform',
    description: 'Build, deploy, and manage AI assistants for African businesses. Voice AI, chatbots, and automation solutions.',
    keywords: ['AI', 'artificial intelligence', 'voice AI', 'chatbots', 'automation', 'Africa', 'business']
  },
  fr: {
    title: 'AI Labs Africa - Plateforme de Gestion d\'Assistants IA',
    description: 'Construisez, déployez et gérez des assistants IA pour les entreprises africaines. IA vocale, chatbots et solutions d\'automatisation.',
    keywords: ['IA', 'intelligence artificielle', 'IA vocale', 'chatbots', 'automatisation', 'Afrique', 'entreprise']
  },
  ar: {
    title: 'مختبرات الذكاء الاصطناعي أفريقيا - منصة إدارة المساعدين الذكيين',
    description: 'بناء ونشر وإدارة المساعدين الذكيين للشركات الأفريقية. الذكاء الاصطناعي الصوتي والروبوتات المحادثة وحلول الأتمتة.',
    keywords: ['ذكاء اصطناعي', 'روبوتات محادثة', 'أتمتة', 'أفريقيا', 'شركات']
  },
  sw: {
    title: 'AI Labs Africa - Jukwaa la Usimamizi wa Wasaidizi wa AI',
    description: 'Jenga, toa na usimamize wasaidizi wa AI kwa biashara za Kiafrika. AI ya sauti, chatbots, na suluhisho za kujibomoa.',
    keywords: ['AI', 'akili ya bandia', 'AI ya sauti', 'chatbots', 'kujibomoa', 'Afrika', 'biashara']
  },
  pt: {
    title: 'AI Labs Africa - Plataforma de Gestão de Assistentes IA',
    description: 'Construa, implemente e gerencie assistentes IA para empresas africanas. IA de voz, chatbots e soluções de automação.',
    keywords: ['IA', 'inteligência artificial', 'IA de voz', 'chatbots', 'automação', 'África', 'negócios']
  }
};

// Page-specific SEO configurations
export const PAGE_SEO_CONFIGS: Record<string, SEOConfig> = {
  '/': {
    title: 'AI Labs Africa - AI Assistant Management Platform',
    description: 'Build, deploy, and manage AI assistants for African businesses. Voice AI, chatbots, and automation solutions.',
    keywords: ['AI', 'artificial intelligence', 'voice AI', 'chatbots', 'automation', 'Africa', 'business'],
    ogType: 'website',
    canonical: 'https://ailabsafrica.com'
  },
  '/dashboard': {
    title: 'Dashboard - AI Labs Africa',
    description: 'Manage your AI assistants, templates, and analytics from your personalized dashboard.',
    keywords: ['dashboard', 'AI management', 'analytics', 'templates'],
    ogType: 'website'
  },
  '/templates': {
    title: 'AI Templates - AI Labs Africa',
    description: 'Browse and customize AI assistant templates for various business use cases.',
    keywords: ['AI templates', 'assistant templates', 'customization', 'business use cases'],
    ogType: 'website'
  },
  '/subscription': {
    title: 'Subscription Plans - AI Labs Africa',
    description: 'Choose the perfect subscription plan for your AI assistant needs.',
    keywords: ['subscription', 'pricing', 'plans', 'AI assistant'],
    ogType: 'website'
  },
  '/team': {
    title: 'Team Management - AI Labs Africa',
    description: 'Collaborate with your team members on AI assistant projects.',
    keywords: ['team management', 'collaboration', 'team members', 'projects'],
    ogType: 'website'
  },
  '/marketing': {
    title: 'Marketing Tools - AI Labs Africa',
    description: 'Leverage AI-powered marketing tools and referral programs.',
    keywords: ['marketing', 'referral program', 'AI tools', 'lead generation'],
    ogType: 'website'
  }
};

// Structured data schemas
export const ORGANIZATION_SCHEMA: StructuredData = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'AI Labs Africa',
  url: 'https://ailabsafrica.com',
  logo: 'https://ailabsafrica.com/logo.png',
  description: 'AI Labs Africa is a leading platform for building and managing AI assistants for African businesses.',
  address: {
    '@type': 'PostalAddress',
    addressCountry: 'Africa'
  },
  contactPoint: {
    '@type': 'ContactPoint',
    contactType: 'customer service',
    email: 'contact@ailabsafrica.com'
  },
  sameAs: [
    'https://twitter.com/ailabsafrica',
    'https://linkedin.com/company/ailabsafrica',
    'https://facebook.com/ailabsafrica'
  ]
};

export const WEBSITE_SCHEMA: StructuredData = {
  '@context': 'https://schema.org',
  '@type': 'WebSite',
  name: 'AI Labs Africa',
  url: 'https://ailabsafrica.com',
  description: 'AI Assistant Management Platform for African Businesses',
  potentialAction: {
    '@type': 'SearchAction',
    target: 'https://ailabsafrica.com/search?q={search_term_string}',
    'query-input': 'required name=search_term_string'
  }
};

export const SOFTWARE_APPLICATION_SCHEMA: StructuredData = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'AI Labs Africa Platform',
  applicationCategory: 'BusinessApplication',
  operatingSystem: 'Web Browser',
  description: 'AI Assistant Management Platform for African Businesses',
  url: 'https://ailabsafrica.com',
  author: {
    '@type': 'Organization',
    name: 'AI Labs Africa'
  },
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'USD'
  }
};

// SEO utility functions
export function generateCanonicalUrl(path: string, language: string = 'en'): string {
  const baseUrl = 'https://ailabsafrica.com';
  const langPrefix = language === 'en' ? '' : `/${language}`;
  return `${baseUrl}${langPrefix}${path}`;
}

export function generateAlternateLanguages(currentPath: string): Array<{ language: string; url: string }> {
  const languages = ['en', 'fr', 'ar', 'sw', 'pt'];
  return languages.map(lang => ({
    language: lang,
    url: generateCanonicalUrl(currentPath, lang)
  }));
}

export function generateStructuredData(type: string, data: any): StructuredData {
  const baseSchema = {
    '@context': 'https://schema.org',
    '@type': type
  };
  
  return {
    ...baseSchema,
    ...data
  };
}

export function generateBreadcrumbSchema(items: Array<{ name: string; url: string }>): StructuredData {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url
    }))
  };
}

export function generateFAQSchema(faqs: Array<{ question: string; answer: string }>): StructuredData {
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map(faq => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer
      }
    }))
  };
}

export function generateProductSchema(product: {
  name: string;
  description: string;
  url: string;
  image?: string;
  price?: string;
  currency?: string;
}): StructuredData {
  return {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    description: product.description,
    url: product.url,
    ...(product.image && { image: product.image }),
    ...(product.price && {
      offers: {
        '@type': 'Offer',
        price: product.price,
        priceCurrency: product.currency || 'USD',
        availability: 'https://schema.org/InStock'
      }
    })
  };
}

// SEO validation functions
export function validateSEOConfig(config: SEOConfig): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (!config.title || config.title.length < 10) {
    errors.push('Title should be at least 10 characters long');
  }
  
  if (!config.description || config.description.length < 50) {
    errors.push('Description should be at least 50 characters long');
  }
  
  if (config.description && config.description.length > 160) {
    errors.push('Description should not exceed 160 characters');
  }
  
  if (!config.keywords || config.keywords.length === 0) {
    errors.push('Keywords are required');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

// SEO performance tracking
export function trackSEOMetrics(metrics: {
  pageLoadTime: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
}) {
  // Send to analytics service
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', 'seo_metrics', {
      page_load_time: metrics.pageLoadTime,
      first_contentful_paint: metrics.firstContentfulPaint,
      largest_contentful_paint: metrics.largestContentfulPaint,
      cumulative_layout_shift: metrics.cumulativeLayoutShift
    });
  }
}

// Export types for use in components
export type { SEOConfig, StructuredData, PageSEOData };
