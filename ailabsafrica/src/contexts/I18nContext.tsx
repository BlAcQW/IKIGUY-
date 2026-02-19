import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { supabase } from '@/integrations/supabase/client';

interface I18nContextType {
  currentLanguage: string;
  changeLanguage: (languageCode: string) => Promise<void>;
  isRTL: boolean;
  loading: boolean;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

interface I18nProviderProps {
  children: ReactNode;
}

export const I18nProvider: React.FC<I18nProviderProps> = ({ children }) => {
  const { i18n } = useTranslation();
  const [currentLanguage, setCurrentLanguage] = useState(i18n.language);
  const [isRTL, setIsRTL] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load user's language preference on mount
    loadUserLanguagePreference();
  }, []);

  const loadUserLanguagePreference = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const { data: result, error } = await supabase.functions.invoke('manage-i18n', {
        body: {
          action: 'get_user_language'
        }
      });

      if (!error && result) {
        if (result.success && result.data) {
          const languageCode = result.data.language_code;
          setCurrentLanguage(languageCode);
          setIsRTL(result.data.is_rtl);
          
          // Update i18n language if different
          if (i18n.language !== languageCode) {
            await i18n.changeLanguage(languageCode);
          }
          
          // Update document direction
          document.documentElement.dir = result.data.is_rtl ? 'rtl' : 'ltr';
        }
      }
    } catch (error) {
      console.error('Error loading user language preference:', error);
    }
  };

  const changeLanguage = async (languageCode: string) => {
    try {
      setLoading(true);
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        throw new Error('User not authenticated');
      }

      const { data: result, error } = await supabase.functions.invoke('manage-i18n', {
        body: {
          action: 'update_user_language',
          languageCode
        }
      });

      if (error) {
        throw new Error('Failed to update language preference');
      }
      if (result.success) {
        // Update i18n language
        await i18n.changeLanguage(languageCode);
        setCurrentLanguage(languageCode);
        
        // Update RTL state based on language
        const isRTLLanguage = languageCode === 'ar';
        setIsRTL(isRTLLanguage);
        
        // Update document direction
        document.documentElement.dir = isRTLLanguage ? 'rtl' : 'ltr';
      }
    } catch (error) {
      console.error('Error changing language:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const value: I18nContextType = {
    currentLanguage,
    changeLanguage,
    isRTL,
    loading,
  };

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = (): I18nContextType => {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};
