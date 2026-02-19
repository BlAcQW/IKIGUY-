import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { Globe, Check, AlertCircle, ChevronDown } from 'lucide-react';

interface LanguageMetadata {
  language_code: string;
  language_name: string;
  native_name: string;
  country_codes: string[];
  is_rtl: boolean;
  is_active: boolean;
  completion_percentage: number;
  last_updated: string;
}

interface UserLanguagePreference {
  language_code: string;
  country_code?: string;
  timezone: string;
  date_format: string;
  time_format: string;
  currency_code: string;
  number_format: string;
  is_rtl: boolean;
}

const LanguageSwitcher: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [languages, setLanguages] = useState<LanguageMetadata[]>([]);
  const [userPreference, setUserPreference] = useState<UserLanguagePreference | null>(null);
  const [currentLanguage, setCurrentLanguage] = useState(i18n.language);
  const [isOpen, setIsOpen] = useState(false);
  const [closeTimeout, setCloseTimeout] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadLanguages();
    loadUserPreference();
  }, []);

  const loadLanguages = async () => {
    try {
      setLoading(true);
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session) {
        const { data: result, error } = await supabase.functions.invoke('manage-i18n', {
          body: {
            action: 'get_language_metadata'
          }
        });

        if (!error && result?.success) {
          setLanguages(result.data);
        } else {
          // Fallback to default languages if API fails
          setLanguages([
            {
              language_code: 'en',
              language_name: 'English',
              native_name: 'English',
              country_codes: ['US', 'GB'],
              is_rtl: false,
              is_active: true,
              completion_percentage: 100,
              last_updated: new Date().toISOString()
            },
            {
              language_code: 'fr',
              language_name: 'French',
              native_name: 'Français',
              country_codes: ['FR', 'CA'],
              is_rtl: false,
              is_active: true,
              completion_percentage: 85,
              last_updated: new Date().toISOString()
            },
            {
              language_code: 'ar',
              language_name: 'Arabic',
              native_name: 'العربية',
              country_codes: ['SA', 'EG'],
              is_rtl: true,
              is_active: true,
              completion_percentage: 75,
              last_updated: new Date().toISOString()
            },
            {
              language_code: 'sw',
              language_name: 'Swahili',
              native_name: 'Kiswahili',
              country_codes: ['KE', 'TZ'],
              is_rtl: false,
              is_active: true,
              completion_percentage: 60,
              last_updated: new Date().toISOString()
            },
            {
              language_code: 'pt',
              language_name: 'Portuguese',
              native_name: 'Português',
              country_codes: ['PT', 'BR'],
              is_rtl: false,
              is_active: true,
              completion_percentage: 70,
              last_updated: new Date().toISOString()
            }
          ]);
        }
      }
    } catch (error) {
      console.error('Error loading languages:', error);
      // Set fallback languages
      setLanguages([
        {
          language_code: 'en',
          language_name: 'English',
          native_name: 'English',
          country_codes: ['US', 'GB'],
          is_rtl: false,
          is_active: true,
          completion_percentage: 100,
          last_updated: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadUserPreference = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session) {
        const { data: result, error } = await supabase.functions.invoke('manage-i18n', {
          body: {
            action: 'get_user_language'
          }
        });

        if (!error && result?.success && result.data) {
          setUserPreference(result.data);
          setCurrentLanguage(result.data.language_code);
        }
      }
    } catch (error) {
      console.error('Error loading user preference:', error);
    }
  };

  const handleLanguageChange = async (languageCode: string) => {
    try {
      setLoading(true);
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session) {
        const { data: result, error } = await supabase.functions.invoke('manage-i18n', {
          body: {
            action: 'update_user_language',
            languageCode
          }
        });

        if (error) {
          throw new Error('Failed to update language preference');
        }

        if (result?.success) {
          await i18n.changeLanguage(languageCode);
          setCurrentLanguage(languageCode);
          
          const selectedLanguage = languages.find(lang => lang.language_code === languageCode);
          if (selectedLanguage) {
            setUserPreference({
              language_code: languageCode,
              country_code: selectedLanguage.country_codes[0],
              timezone: 'UTC',
              date_format: 'MM/DD/YYYY',
              time_format: '12h',
              currency_code: 'USD',
              number_format: 'en-US',
              is_rtl: selectedLanguage.is_rtl
            });
          }

          toast({
            title: 'Language Updated',
            description: `Switched to ${selectedLanguage?.native_name || languageCode}`,
          });

          // Update document direction for RTL languages
          document.documentElement.dir = selectedLanguage?.is_rtl ? 'rtl' : 'ltr';
        }
      } else {
        // For non-authenticated users, just change the language locally
        await i18n.changeLanguage(languageCode);
        setCurrentLanguage(languageCode);
        
        const selectedLanguage = languages.find(lang => lang.language_code === languageCode);
        if (selectedLanguage) {
          document.documentElement.dir = selectedLanguage.is_rtl ? 'rtl' : 'ltr';
        }
      }
    } catch (error) {
      console.error('Error changing language:', error);
      toast({
        title: 'Error',
        description: 'Failed to update language preference',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
      setIsOpen(false);
    }
  };

  const handleMouseEnter = () => {
    if (closeTimeout) {
      clearTimeout(closeTimeout);
      setCloseTimeout(null);
    }
    setIsOpen(true);
  };

  const handleMouseLeave = () => {
    const timeout = setTimeout(() => setIsOpen(false), 300);
    setCloseTimeout(timeout);
  };

  const getLanguageFlag = (countryCodes: string[]): string => {
    if (!countryCodes.length) return '🌐';
    
    const countryCode = countryCodes[0];
    const codePoints = countryCode
      .toUpperCase()
      .split('')
      .map(char => 127397 + char.charCodeAt(0));
    
    return String.fromCodePoint(...codePoints);
  };

  const getCurrentLanguage = () => {
    const current = languages.find(lang => lang.language_code === currentLanguage);
    return current || languages[0];
  };

  const currentLang = getCurrentLanguage();

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="ghost" 
          size="sm" 
          className="flex items-center gap-2 hover:bg-accent transition-colors duration-200 group"
          disabled={loading}
          onMouseEnter={handleMouseEnter}
        >
          <span className="text-lg">
            {getLanguageFlag(currentLang.country_codes)}
          </span>
          <span className="hidden sm:inline text-sm font-medium">
            {currentLang.native_name}
          </span>
          <span className="sm:hidden text-xs font-medium">
            {currentLang.language_code.toUpperCase()}
          </span>
          <ChevronDown className={`h-3 w-3 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        align="end" 
        className="w-56 sm:w-64 animate-in slide-in-from-top-2 duration-200 max-h-[60vh] overflow-y-auto"
        onMouseLeave={handleMouseLeave}
      >
        <DropdownMenuLabel className="flex items-center gap-2">
          <Globe className="h-4 w-4" />
          Choose Language
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {languages.map((language) => (
          <DropdownMenuItem
            key={language.language_code}
            onClick={() => handleLanguageChange(language.language_code)}
            className="flex items-center justify-between cursor-pointer hover:bg-accent transition-colors duration-150"
            disabled={loading}
          >
            <div className="flex items-center gap-3">
              <span className="text-lg">
                {getLanguageFlag(language.country_codes)}
              </span>
              <div className="flex flex-col">
                <span className="font-medium">{language.native_name}</span>
                <span className="text-xs text-muted-foreground">
                  {language.language_name}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {language.is_rtl && (
                <Badge variant="outline" className="text-xs">RTL</Badge>
              )}
              {language.language_code === currentLanguage && (
                <Check className="h-4 w-4 text-primary" />
              )}
              {language.completion_percentage < 100 && (
                <Badge variant="secondary" className="text-xs">
                  {language.completion_percentage}%
                </Badge>
              )}
            </div>
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <div className="px-2 py-1.5 text-xs text-muted-foreground">
          Translation progress shown for each language
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default LanguageSwitcher;



