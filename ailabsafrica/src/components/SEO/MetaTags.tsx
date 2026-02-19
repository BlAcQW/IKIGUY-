/**
 * Meta Tags Component
 * Dynamically manages meta tags using React Helmet Async
 */

import React from 'react';
import { Helmet } from 'react-helmet-async';
import { useSEO } from './SeoProvider';
import { SEOConfig } from '@/lib/seo';

interface MetaTagsProps {
  config?: Partial<SEOConfig>;
  structuredData?: Array<{ [key: string]: any }>;
}

const MetaTags: React.FC<MetaTagsProps> = ({ config, structuredData = [] }) => {
  const { seoConfig } = useSEO();
  
  // Merge provided config with current SEO config
  const finalConfig = { ...seoConfig, ...config };

  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <title>{finalConfig.title}</title>
      <meta name="description" content={finalConfig.description} />
      {finalConfig.keywords && (
        <meta name="keywords" content={finalConfig.keywords.join(', ')} />
      )}
      
      {/* Canonical URL */}
      {finalConfig.canonical && (
        <link rel="canonical" href={finalConfig.canonical} />
      )}
      
      {/* Language and Direction */}
      <html lang={finalConfig.language || 'en'} />
      <meta name="language" content={finalConfig.language || 'en'} />
      
      {/* Robots Meta */}
      {finalConfig.noIndex && <meta name="robots" content="noindex" />}
      {finalConfig.noFollow && <meta name="robots" content="nofollow" />}
      {!finalConfig.noIndex && !finalConfig.noFollow && (
        <meta name="robots" content="index, follow" />
      )}
      
      {/* Open Graph Tags */}
      <meta property="og:title" content={finalConfig.title} />
      <meta property="og:description" content={finalConfig.description} />
      <meta property="og:type" content={finalConfig.ogType || 'website'} />
      <meta property="og:url" content={finalConfig.canonical || window.location.href} />
      <meta property="og:site_name" content="AI Labs Africa" />
      <meta property="og:locale" content={finalConfig.language || 'en_US'} />
      {finalConfig.ogImage && (
        <meta property="og:image" content={finalConfig.ogImage} />
      )}
      
      {/* Twitter Card Tags */}
      <meta name="twitter:card" content={finalConfig.twitterCard || 'summary_large_image'} />
      <meta name="twitter:title" content={finalConfig.title} />
      <meta name="twitter:description" content={finalConfig.description} />
      <meta name="twitter:site" content="@ailabsafrica" />
      <meta name="twitter:creator" content="@ailabsafrica" />
      {finalConfig.ogImage && (
        <meta name="twitter:image" content={finalConfig.ogImage} />
      )}
      
      {/* Hreflang Tags for Language Alternatives */}
      {finalConfig.alternateLanguages?.map(({ language, url }) => (
        <link
          key={language}
          rel="alternate"
          hrefLang={language}
          href={url}
        />
      ))}
      
      {/* Default hreflang for x-default */}
      {finalConfig.canonical && (
        <link rel="alternate" hrefLang="x-default" href={finalConfig.canonical} />
      )}
      
      {/* Additional Meta Tags */}
      <meta name="author" content="AI Labs Africa" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta name="theme-color" content="#2563eb" />
      <meta name="msapplication-TileColor" content="#2563eb" />
      
      {/* Structured Data */}
      {structuredData.map((data, index) => (
        <script
          key={index}
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(data)
          }}
        />
      ))}
      
      {/* Favicon and App Icons */}
      <link rel="icon" type="image/x-icon" href="/favicon.ico" />
      <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
      <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
      <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
      <link rel="manifest" href="/site.webmanifest" />
      
      {/* Preconnect to External Domains */}
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link rel="preconnect" href="https://www.google-analytics.com" />
      
      {/* DNS Prefetch */}
      <link rel="dns-prefetch" href="//www.google-analytics.com" />
      <link rel="dns-prefetch" href="//fonts.googleapis.com" />
    </Helmet>
  );
};

export default MetaTags;
