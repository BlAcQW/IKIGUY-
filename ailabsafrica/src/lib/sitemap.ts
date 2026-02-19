/**
 * Sitemap Generation Logic
 * Creates dynamic XML sitemaps with language variants
 */

import { PageSEOData } from './seo';

export interface SitemapConfig {
  baseUrl: string;
  languages: string[];
  defaultLanguage: string;
  pages: PageSEOData[];
  lastModified: string;
}

// Default sitemap configuration
export const DEFAULT_SITEMAP_CONFIG: SitemapConfig = {
  baseUrl: 'https://ailabsafrica.com',
  languages: ['en', 'fr', 'ar', 'sw', 'pt'],
  defaultLanguage: 'en',
  pages: [
    {
      path: '/',
      title: 'AI Labs Africa - AI Assistant Management Platform',
      description: 'Build, deploy, and manage AI assistants for African businesses.',
      keywords: ['AI', 'artificial intelligence', 'voice AI', 'chatbots', 'automation', 'Africa', 'business'],
      lastModified: new Date().toISOString(),
      changeFrequency: 'weekly',
      priority: 1.0,
      language: 'en'
    },
    {
      path: '/dashboard',
      title: 'Dashboard - AI Labs Africa',
      description: 'Manage your AI assistants, templates, and analytics.',
      keywords: ['dashboard', 'AI management', 'analytics', 'templates'],
      lastModified: new Date().toISOString(),
      changeFrequency: 'daily',
      priority: 0.9,
      language: 'en'
    },
    {
      path: '/templates',
      title: 'AI Templates - AI Labs Africa',
      description: 'Browse and customize AI assistant templates.',
      keywords: ['AI templates', 'assistant templates', 'customization'],
      lastModified: new Date().toISOString(),
      changeFrequency: 'weekly',
      priority: 0.8,
      language: 'en'
    },
    {
      path: '/subscription',
      title: 'Subscription Plans - AI Labs Africa',
      description: 'Choose the perfect subscription plan for your AI assistant needs.',
      keywords: ['subscription', 'pricing', 'plans', 'AI assistant'],
      lastModified: new Date().toISOString(),
      changeFrequency: 'monthly',
      priority: 0.7,
      language: 'en'
    },
    {
      path: '/team',
      title: 'Team Management - AI Labs Africa',
      description: 'Collaborate with your team members on AI assistant projects.',
      keywords: ['team management', 'collaboration', 'team members'],
      lastModified: new Date().toISOString(),
      changeFrequency: 'weekly',
      priority: 0.6,
      language: 'en'
    },
    {
      path: '/marketing',
      title: 'Marketing Tools - AI Labs Africa',
      description: 'Leverage AI-powered marketing tools and referral programs.',
      keywords: ['marketing', 'referral program', 'AI tools', 'lead generation'],
      lastModified: new Date().toISOString(),
      changeFrequency: 'weekly',
      priority: 0.6,
      language: 'en'
    }
  ],
  lastModified: new Date().toISOString()
};

// Language-specific page configurations
export const LANGUAGE_PAGE_CONFIGS: Record<string, Partial<PageSEOData>[]> = {
  fr: [
    {
      path: '/',
      title: 'AI Labs Africa - Plateforme de Gestion d\'Assistants IA',
      description: 'Construisez, déployez et gérez des assistants IA pour les entreprises africaines.',
      keywords: ['IA', 'intelligence artificielle', 'IA vocale', 'chatbots', 'automatisation', 'Afrique', 'entreprise'],
      language: 'fr'
    },
    {
      path: '/dashboard',
      title: 'Tableau de Bord - AI Labs Africa',
      description: 'Gérez vos assistants IA, modèles et analyses.',
      keywords: ['tableau de bord', 'gestion IA', 'analyses', 'modèles'],
      language: 'fr'
    }
  ],
  ar: [
    {
      path: '/',
      title: 'مختبرات الذكاء الاصطناعي أفريقيا - منصة إدارة المساعدين الذكيين',
      description: 'بناء ونشر وإدارة المساعدين الذكيين للشركات الأفريقية.',
      keywords: ['ذكاء اصطناعي', 'روبوتات محادثة', 'أتمتة', 'أفريقيا', 'شركات'],
      language: 'ar'
    },
    {
      path: '/dashboard',
      title: 'لوحة التحكم - مختبرات الذكاء الاصطناعي أفريقيا',
      description: 'إدارة المساعدين الذكيين والقوالب والتحليلات.',
      keywords: ['لوحة التحكم', 'إدارة الذكاء الاصطناعي', 'تحليلات', 'قوالب'],
      language: 'ar'
    }
  ],
  sw: [
    {
      path: '/',
      title: 'AI Labs Africa - Jukwaa la Usimamizi wa Wasaidizi wa AI',
      description: 'Jenga, toa na usimamize wasaidizi wa AI kwa biashara za Kiafrika.',
      keywords: ['AI', 'akili ya bandia', 'AI ya sauti', 'chatbots', 'kujibomoa', 'Afrika', 'biashara'],
      language: 'sw'
    },
    {
      path: '/dashboard',
      title: 'Dashibodi - AI Labs Africa',
      description: 'Simamia wasaidizi wa AI, viwango na uchambuzi.',
      keywords: ['dashibodi', 'usimamizi wa AI', 'uchambuzi', 'viwango'],
      language: 'sw'
    }
  ],
  pt: [
    {
      path: '/',
      title: 'AI Labs Africa - Plataforma de Gestão de Assistentes IA',
      description: 'Construa, implemente e gerencie assistentes IA para empresas africanas.',
      keywords: ['IA', 'inteligência artificial', 'IA de voz', 'chatbots', 'automação', 'África', 'negócios'],
      language: 'pt'
    },
    {
      path: '/dashboard',
      title: 'Painel de Controle - AI Labs Africa',
      description: 'Gerencie seus assistentes IA, modelos e análises.',
      keywords: ['painel de controle', 'gestão de IA', 'análises', 'modelos'],
      language: 'pt'
    }
  ]
};

// Generate URL for a specific language and path
export function generateLanguageUrl(baseUrl: string, path: string, language: string, defaultLanguage: string): string {
  const langPrefix = language === defaultLanguage ? '' : `/${language}`;
  return `${baseUrl}${langPrefix}${path}`;
}

// Generate sitemap XML content
export function generateSitemapXML(config: SitemapConfig): string {
  const { baseUrl, languages, defaultLanguage, pages, lastModified } = config;
  
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" ';
  xml += 'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n';
  
  // Generate URLs for each page and language
  pages.forEach(page => {
    languages.forEach(language => {
      const url = generateLanguageUrl(baseUrl, page.path, language, defaultLanguage);
      
      xml += '  <url>\n';
      xml += `    <loc>${url}</loc>\n`;
      xml += `    <lastmod>${page.lastModified}</lastmod>\n`;
      xml += `    <changefreq>${page.changeFrequency}</changefreq>\n`;
      xml += `    <priority>${page.priority}</priority>\n`;
      
      // Add alternate language links
      languages.forEach(altLang => {
        const altUrl = generateLanguageUrl(baseUrl, page.path, altLang, defaultLanguage);
        xml += `    <xhtml:link rel="alternate" hreflang="${altLang}" href="${altUrl}" />\n`;
      });
      
      // Add x-default link
      const defaultUrl = generateLanguageUrl(baseUrl, page.path, defaultLanguage, defaultLanguage);
      xml += `    <xhtml:link rel="alternate" hreflang="x-default" href="${defaultUrl}" />\n`;
      
      xml += '  </url>\n';
    });
  });
  
  xml += '</urlset>';
  return xml;
}

// Generate sitemap index XML
export function generateSitemapIndexXML(sitemaps: Array<{ url: string; lastModified: string }>): string {
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  xml += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';
  
  sitemaps.forEach(sitemap => {
    xml += '  <sitemap>\n';
    xml += `    <loc>${sitemap.url}</loc>\n`;
    xml += `    <lastmod>${sitemap.lastModified}</lastmod>\n`;
    xml += '  </sitemap>\n';
  });
  
  xml += '</sitemapindex>';
  return xml;
}

// Generate robots.txt content
export function generateRobotsTxt(baseUrl: string, sitemapUrl: string): string {
  return `User-agent: *
Allow: /

# Disallow admin and private areas
Disallow: /admin/
Disallow: /private/
Disallow: /api/
Disallow: /_next/

# Allow important pages
Allow: /dashboard
Allow: /templates
Allow: /subscription
Allow: /team
Allow: /marketing

# Sitemap
Sitemap: ${sitemapUrl}

# Crawl-delay
Crawl-delay: 1`;
}

// Generate language-specific sitemap
export function generateLanguageSitemap(
  baseUrl: string,
  pages: PageSEOData[],
  language: string,
  defaultLanguage: string
): string {
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
  xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';
  
  pages.forEach(page => {
    const url = generateLanguageUrl(baseUrl, page.path, language, defaultLanguage);
    
    xml += '  <url>\n';
    xml += `    <loc>${url}</loc>\n`;
    xml += `    <lastmod>${page.lastModified}</lastmod>\n`;
    xml += `    <changefreq>${page.changeFrequency}</changefreq>\n`;
    xml += `    <priority>${page.priority}</priority>\n`;
    xml += '  </url>\n';
  });
  
  xml += '</urlset>';
  return xml;
}

// Merge language-specific configurations with default pages
export function mergeLanguageConfigs(
  defaultPages: PageSEOData[],
  languageConfigs: Record<string, Partial<PageSEOData>[]>
): PageSEOData[] {
  const mergedPages: PageSEOData[] = [];
  
  defaultPages.forEach(defaultPage => {
    // Add default page
    mergedPages.push(defaultPage);
    
    // Add language-specific variations
    Object.entries(languageConfigs).forEach(([language, configs]) => {
      const langConfig = configs.find(config => config.path === defaultPage.path);
      if (langConfig) {
        mergedPages.push({
          ...defaultPage,
          ...langConfig,
          language
        });
      }
    });
  });
  
  return mergedPages;
}

// Validate sitemap configuration
export function validateSitemapConfig(config: SitemapConfig): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];
  
  if (!config.baseUrl || !config.baseUrl.startsWith('http')) {
    errors.push('Base URL must be a valid HTTP/HTTPS URL');
  }
  
  if (!config.languages || config.languages.length === 0) {
    errors.push('At least one language must be specified');
  }
  
  if (!config.defaultLanguage || !config.languages.includes(config.defaultLanguage)) {
    errors.push('Default language must be one of the specified languages');
  }
  
  if (!config.pages || config.pages.length === 0) {
    errors.push('At least one page must be specified');
  }
  
  config.pages.forEach((page, index) => {
    if (!page.path || !page.path.startsWith('/')) {
      errors.push(`Page ${index + 1}: Path must start with '/'`);
    }
    
    if (!page.title || page.title.length < 10) {
      errors.push(`Page ${index + 1}: Title must be at least 10 characters long`);
    }
    
    if (!page.description || page.description.length < 50) {
      errors.push(`Page ${index + 1}: Description must be at least 50 characters long`);
    }
    
    if (page.priority < 0 || page.priority > 1) {
      errors.push(`Page ${index + 1}: Priority must be between 0 and 1`);
    }
  });
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

// Export types and configurations
export type { SitemapConfig };
