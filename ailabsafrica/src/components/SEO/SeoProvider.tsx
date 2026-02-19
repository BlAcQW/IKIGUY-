/**
 * SEO Context Provider
 * Manages global SEO state and provides SEO functionality throughout the application
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useLocation } from 'react-router-dom';
// import { useTranslation } from 'react-i18next';
import { SEOConfig, DEFAULT_SEO_CONFIG, PAGE_SEO_CONFIGS, LANGUAGE_SEO_CONFIGS } from '@/lib/seo';

interface SEOContextType {
  seoConfig: SEOConfig;
  updateSEO: (config: Partial<SEOConfig>) => void;
  currentPage: string;
  currentLanguage: string;
  loading: boolean;
}

const SEOContext = createContext<SEOContextType | undefined>(undefined);

interface SeoProviderProps {
  children: ReactNode;
}

export const SeoProvider: React.FC<SeoProviderProps> = ({ children }) => {
  const location = useLocation();
  // const { i18n } = useTranslation();
  const [seoConfig, setSeoConfig] = useState<SEOConfig>(DEFAULT_SEO_CONFIG);
  const [loading, setLoading] = useState(false);

  const currentPage = location.pathname;
  const currentLanguage = 'en'; // Default to English since i18n is disabled

  // Update SEO configuration based on current page and language
  useEffect(() => {
    const updatePageSEO = async () => {
      setLoading(true);
      
      try {
        // Get page-specific SEO config
        const pageConfig = PAGE_SEO_CONFIGS[currentPage] || DEFAULT_SEO_CONFIG;
        
        // Get language-specific SEO config
        const languageConfig = LANGUAGE_SEO_CONFIGS[currentLanguage] || {};
        
        // Merge configurations
        const mergedConfig: SEOConfig = {
          ...DEFAULT_SEO_CONFIG,
          ...pageConfig,
          ...languageConfig,
          language: currentLanguage,
          canonical: pageConfig.canonical || `https://ailabsafrica.com${currentPage}`,
          alternateLanguages: generateAlternateLanguages(currentPage)
        };

        setSeoConfig(mergedConfig);
      } catch (error) {
        console.error('Error updating SEO configuration:', error);
        setSeoConfig(DEFAULT_SEO_CONFIG);
      } finally {
        setLoading(false);
      }
    };

    updatePageSEO();
  }, [currentPage, currentLanguage]);

  // Generate alternate language URLs
  const generateAlternateLanguages = (path: string) => {
    const languages = ['en', 'fr', 'ar', 'sw', 'pt'];
    return languages.map(lang => ({
      language: lang,
      url: `https://ailabsafrica.com${lang === 'en' ? '' : `/${lang}`}${path}`
    }));
  };

  // Update SEO configuration
  const updateSEO = (config: Partial<SEOConfig>) => {
    setSeoConfig(prev => ({
      ...prev,
      ...config
    }));
  };

  const value: SEOContextType = {
    seoConfig,
    updateSEO,
    currentPage,
    currentLanguage,
    loading
  };

  return (
    <SEOContext.Provider value={value}>
      {children}
    </SEOContext.Provider>
  );
};

export const useSEO = (): SEOContextType => {
  const context = useContext(SEOContext);
  if (context === undefined) {
    throw new Error('useSEO must be used within a SeoProvider');
  }
  return context;
};
