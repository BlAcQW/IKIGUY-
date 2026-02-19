/**
 * Structured Data Components
 * Provides reusable JSON-LD schema components for rich snippets
 */

import React from 'react';
import { Helmet } from 'react-helmet-async';
import {
  StructuredData,
  ORGANIZATION_SCHEMA,
  WEBSITE_SCHEMA,
  SOFTWARE_APPLICATION_SCHEMA,
  generateBreadcrumbSchema,
  generateFAQSchema,
  generateProductSchema
} from '@/lib/seo';

interface StructuredDataProps {
  schemas: StructuredData[];
}

const StructuredDataComponent: React.FC<StructuredDataProps> = ({ schemas }) => {
  return (
    <Helmet>
      {schemas.map((schema, index) => (
        <script
          key={index}
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(schema)
          }}
        />
      ))}
    </Helmet>
  );
};

// Organization Schema Component
export const OrganizationSchema: React.FC = () => (
  <StructuredDataComponent schemas={[ORGANIZATION_SCHEMA]} />
);

// Website Schema Component
export const WebsiteSchema: React.FC = () => (
  <StructuredDataComponent schemas={[WEBSITE_SCHEMA]} />
);

// Software Application Schema Component
export const SoftwareApplicationSchema: React.FC = () => (
  <StructuredDataComponent schemas={[SOFTWARE_APPLICATION_SCHEMA]} />
);

// Breadcrumb Schema Component
interface BreadcrumbSchemaProps {
  items: Array<{ name: string; url: string }>;
}

export const BreadcrumbSchema: React.FC<BreadcrumbSchemaProps> = ({ items }) => {
  const schema = generateBreadcrumbSchema(items);
  return <StructuredDataComponent schemas={[schema]} />;
};

// FAQ Schema Component
interface FAQSchemaProps {
  faqs: Array<{ question: string; answer: string }>;
}

export const FAQSchema: React.FC<FAQSchemaProps> = ({ faqs }) => {
  const schema = generateFAQSchema(faqs);
  return <StructuredDataComponent schemas={[schema]} />;
};

// Product Schema Component
interface ProductSchemaProps {
  product: {
    name: string;
    description: string;
    url: string;
    image?: string;
    price?: string;
    currency?: string;
  };
}

export const ProductSchema: React.FC<ProductSchemaProps> = ({ product }) => {
  const schema = generateProductSchema(product);
  return <StructuredDataComponent schemas={[schema]} />;
};

// Article Schema Component
interface ArticleSchemaProps {
  article: {
    headline: string;
    description: string;
    url: string;
    image?: string;
    author?: string;
    datePublished: string;
    dateModified?: string;
  };
}

export const ArticleSchema: React.FC<ArticleSchemaProps> = ({ article }) => {
  const schema: StructuredData = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: article.headline,
    description: article.description,
    url: article.url,
    ...(article.image && { image: article.image }),
    ...(article.author && { author: { '@type': 'Person', name: article.author } }),
    datePublished: article.datePublished,
    ...(article.dateModified && { dateModified: article.dateModified }),
    publisher: {
      '@type': 'Organization',
      name: 'AI Labs Africa',
      logo: {
        '@type': 'ImageObject',
        url: 'https://ailabsafrica.com/logo.png'
      }
    }
  };
  
  return <StructuredDataComponent schemas={[schema]} />;
};

// Service Schema Component
interface ServiceSchemaProps {
  service: {
    name: string;
    description: string;
    url: string;
    provider?: string;
    areaServed?: string;
    serviceType?: string;
  };
}

export const ServiceSchema: React.FC<ServiceSchemaProps> = ({ service }) => {
  const schema: StructuredData = {
    '@context': 'https://schema.org',
    '@type': 'Service',
    name: service.name,
    description: service.description,
    url: service.url,
    ...(service.provider && { provider: { '@type': 'Organization', name: service.provider } }),
    ...(service.areaServed && { areaServed: { '@type': 'Place', name: service.areaServed } }),
    ...(service.serviceType && { serviceType: service.serviceType })
  };
  
  return <StructuredDataComponent schemas={[schema]} />;
};

// Local Business Schema Component
interface LocalBusinessSchemaProps {
  business: {
    name: string;
    description: string;
    url: string;
    address?: {
      streetAddress: string;
      addressLocality: string;
      addressRegion: string;
      postalCode: string;
      addressCountry: string;
    };
    telephone?: string;
    email?: string;
  };
}

export const LocalBusinessSchema: React.FC<LocalBusinessSchemaProps> = ({ business }) => {
  const schema: StructuredData = {
    '@context': 'https://schema.org',
    '@type': 'LocalBusiness',
    name: business.name,
    description: business.description,
    url: business.url,
    ...(business.address && {
      address: {
        '@type': 'PostalAddress',
        streetAddress: business.address.streetAddress,
        addressLocality: business.address.addressLocality,
        addressRegion: business.address.addressRegion,
        postalCode: business.address.postalCode,
        addressCountry: business.address.addressCountry
      }
    }),
    ...(business.telephone && { telephone: business.telephone }),
    ...(business.email && { email: business.email })
  };
  
  return <StructuredDataComponent schemas={[schema]} />;
};

// Event Schema Component
interface EventSchemaProps {
  event: {
    name: string;
    description: string;
    url: string;
    startDate: string;
    endDate?: string;
    location?: {
      name: string;
      address?: string;
    };
    organizer?: string;
  };
}

export const EventSchema: React.FC<EventSchemaProps> = ({ event }) => {
  const schema: StructuredData = {
    '@context': 'https://schema.org',
    '@type': 'Event',
    name: event.name,
    description: event.description,
    url: event.url,
    startDate: event.startDate,
    ...(event.endDate && { endDate: event.endDate }),
    ...(event.location && {
      location: {
        '@type': 'Place',
        name: event.location.name,
        ...(event.location.address && { address: event.location.address })
      }
    }),
    ...(event.organizer && { organizer: { '@type': 'Organization', name: event.organizer } })
  };
  
  return <StructuredDataComponent schemas={[schema]} />;
};

// Custom Schema Component
interface CustomSchemaProps {
  schema: StructuredData;
}

export const CustomSchema: React.FC<CustomSchemaProps> = ({ schema }) => {
  return <StructuredDataComponent schemas={[schema]} />;
};

export default StructuredDataComponent;
