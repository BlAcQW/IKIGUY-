import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import LanguageSwitcher from '../components/LanguageSwitcher';

// Mock the translation hook
const mockT = vi.fn((key) => key);
const mockI18n = {
  language: 'en',
  changeLanguage: vi.fn(),
};

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: mockT,
    i18n: mockI18n,
  }),
}));

// Mock the toast hook
const mockToast = vi.fn();
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock Supabase client
const mockSupabase = {
  auth: {
    getSession: vi.fn(() => Promise.resolve({
      data: {
        session: {
          access_token: 'mock-token'
        }
      }
    }))
  }
};

vi.mock('@/integrations/supabase/client', () => ({
  supabase: mockSupabase,
}));

// Mock fetch
global.fetch = vi.fn();

// Mock document.documentElement
Object.defineProperty(document, 'documentElement', {
  value: {
    dir: 'ltr',
  },
  writable: true,
});

describe('LanguageSwitcher', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockT.mockImplementation((key) => key);
  });

  it('renders language switcher component', () => {
    render(<LanguageSwitcher />);
    
    expect(screen.getByText('common.language')).toBeInTheDocument();
    expect(screen.getByText('Choose your preferred language for the application')).toBeInTheDocument();
  });

  it('shows loading state initially', () => {
    render(<LanguageSwitcher />);
    
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('loads and displays languages', async () => {
    const mockLanguages = [
      {
        language_code: 'en',
        language_name: 'English',
        native_name: 'English',
        country_codes: ['US', 'GB'],
        is_rtl: false,
        is_active: true,
        completion_percentage: 100,
        last_updated: '2025-01-21T00:00:00Z'
      },
      {
        language_code: 'fr',
        language_name: 'French',
        native_name: 'Français',
        country_codes: ['FR'],
        is_rtl: false,
        is_active: true,
        completion_percentage: 75,
        last_updated: '2025-01-21T00:00:00Z'
      }
    ];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: true, data: mockLanguages })
    });

    render(<LanguageSwitcher />);

    await waitFor(() => {
      expect(screen.getByText('Select Language')).toBeInTheDocument();
    });
  });

  it('handles language change', async () => {
    const mockLanguages = [
      {
        language_code: 'en',
        language_name: 'English',
        native_name: 'English',
        country_codes: ['US'],
        is_rtl: false,
        is_active: true,
        completion_percentage: 100,
        last_updated: '2025-01-21T00:00:00Z'
      },
      {
        language_code: 'fr',
        language_name: 'French',
        native_name: 'Français',
        country_codes: ['FR'],
        is_rtl: false,
        is_active: true,
        completion_percentage: 75,
        last_updated: '2025-01-21T00:00:00Z'
      }
    ];

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockLanguages })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: { language_code: 'en' } })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: { updated: true } })
      });

    render(<LanguageSwitcher />);

    await waitFor(() => {
      expect(screen.getByText('Select Language')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    fireEvent.click(select);

    await waitFor(() => {
      const frenchOption = screen.getByText('Français');
      fireEvent.click(frenchOption);
    });

    await waitFor(() => {
      expect(mockI18n.changeLanguage).toHaveBeenCalledWith('fr');
      expect(mockToast).toHaveBeenCalledWith({
        title: 'common.success',
        description: 'Language changed to Français',
      });
    });
  });

  it('handles RTL language change', async () => {
    const mockLanguages = [
      {
        language_code: 'ar',
        language_name: 'Arabic',
        native_name: 'العربية',
        country_codes: ['SA'],
        is_rtl: true,
        is_active: true,
        completion_percentage: 50,
        last_updated: '2025-01-21T00:00:00Z'
      }
    ];

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockLanguages })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: { language_code: 'en' } })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: { updated: true } })
      });

    render(<LanguageSwitcher />);

    await waitFor(() => {
      expect(screen.getByText('Select Language')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    fireEvent.click(select);

    await waitFor(() => {
      const arabicOption = screen.getByText('العربية');
      fireEvent.click(arabicOption);
    });

    await waitFor(() => {
      expect(document.documentElement.dir).toBe('rtl');
    });
  });

  it('displays translation progress', async () => {
    const mockLanguages = [
      {
        language_code: 'en',
        language_name: 'English',
        native_name: 'English',
        country_codes: ['US'],
        is_rtl: false,
        is_active: true,
        completion_percentage: 100,
        last_updated: '2025-01-21T00:00:00Z'
      },
      {
        language_code: 'fr',
        language_name: 'French',
        native_name: 'Français',
        country_codes: ['FR'],
        is_rtl: false,
        is_active: true,
        completion_percentage: 75,
        last_updated: '2025-01-21T00:00:00Z'
      }
    ];

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockLanguages })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: { language_code: 'en' } })
      });

    render(<LanguageSwitcher />);

    await waitFor(() => {
      expect(screen.getByText('Translation Progress')).toBeInTheDocument();
      expect(screen.getByText('100.0%')).toBeInTheDocument();
      expect(screen.getByText('75.0%')).toBeInTheDocument();
    });
  });

  it('shows completion badges', async () => {
    const mockLanguages = [
      {
        language_code: 'en',
        language_name: 'English',
        native_name: 'English',
        country_codes: ['US'],
        is_rtl: false,
        is_active: true,
        completion_percentage: 100,
        last_updated: '2025-01-21T00:00:00Z'
      },
      {
        language_code: 'fr',
        language_name: 'French',
        native_name: 'Français',
        country_codes: ['FR'],
        is_rtl: false,
        is_active: true,
        completion_percentage: 50,
        last_updated: '2025-01-21T00:00:00Z'
      }
    ];

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockLanguages })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: { language_code: 'en' } })
      });

    render(<LanguageSwitcher />);

    await waitFor(() => {
      expect(screen.getByText('Complete')).toBeInTheDocument();
      expect(screen.getByText('Incomplete')).toBeInTheDocument();
    });
  });

  it('handles authentication error', async () => {
    mockSupabase.auth.getSession.mockResolvedValueOnce({
      data: { session: null }
    });

    render(<LanguageSwitcher />);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'common.error',
        description: 'User not authenticated',
        variant: 'destructive',
      });
    });
  });

  it('handles API error', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('API Error'));

    render(<LanguageSwitcher />);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'common.error',
        description: 'Failed to load languages',
        variant: 'destructive',
      });
    });
  });

  it('displays current user preference', async () => {
    const mockLanguages = [
      {
        language_code: 'en',
        language_name: 'English',
        native_name: 'English',
        country_codes: ['US'],
        is_rtl: false,
        is_active: true,
        completion_percentage: 100,
        last_updated: '2025-01-21T00:00:00Z'
      }
    ];

    const mockUserPreference = {
      language_code: 'en',
      country_code: 'US',
      timezone: 'UTC',
      date_format: 'MM/DD/YYYY',
      time_format: '12h',
      currency_code: 'USD',
      number_format: 'en-US',
      is_rtl: false
    };

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockLanguages })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockUserPreference })
      });

    render(<LanguageSwitcher />);

    await waitFor(() => {
      expect(screen.getByText('English')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
    });
  });

  it('shows RTL badge for RTL languages', async () => {
    const mockLanguages = [
      {
        language_code: 'ar',
        language_name: 'Arabic',
        native_name: 'العربية',
        country_codes: ['SA'],
        is_rtl: true,
        is_active: true,
        completion_percentage: 50,
        last_updated: '2025-01-21T00:00:00Z'
      }
    ];

    (global.fetch as any)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: mockLanguages })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, data: { language_code: 'en' } })
      });

    render(<LanguageSwitcher />);

    await waitFor(() => {
      expect(screen.getByText('RTL')).toBeInTheDocument();
    });
  });
});
