/**
 * Phone number formatting utilities with country code support.
 */

export interface CountryCode {
  code: string;
  country: string;
  dialCode: string;
  flag: string;
}

/**
 * Common country codes for phone number formatting.
 * Focused on African countries and common international codes.
 */
export const COUNTRY_CODES: CountryCode[] = [
  { code: 'GH', country: 'Ghana', dialCode: '+233', flag: '🇬🇭' },
  { code: 'NG', country: 'Nigeria', dialCode: '+234', flag: '🇳🇬' },
  { code: 'KE', country: 'Kenya', dialCode: '+254', flag: '🇰🇪' },
  { code: 'ZA', country: 'South Africa', dialCode: '+27', flag: '🇿🇦' },
  { code: 'UG', country: 'Uganda', dialCode: '+256', flag: '🇺🇬' },
  { code: 'TZ', country: 'Tanzania', dialCode: '+255', flag: '🇹🇿' },
  { code: 'ET', country: 'Ethiopia', dialCode: '+251', flag: '🇪🇹' },
  { code: 'RW', country: 'Rwanda', dialCode: '+250', flag: '🇷🇼' },
  { code: 'US', country: 'United States', dialCode: '+1', flag: '🇺🇸' },
  { code: 'GB', country: 'United Kingdom', dialCode: '+44', flag: '🇬🇧' },
  { code: 'CA', country: 'Canada', dialCode: '+1', flag: '🇨🇦' },
  { code: 'AU', country: 'Australia', dialCode: '+61', flag: '🇦🇺' },
  { code: 'FR', country: 'France', dialCode: '+33', flag: '🇫🇷' },
  { code: 'DE', country: 'Germany', dialCode: '+49', flag: '🇩🇪' },
  { code: 'IN', country: 'India', dialCode: '+91', flag: '🇮🇳' },
  { code: 'CN', country: 'China', dialCode: '+86', flag: '🇨🇳' },
];

/**
 * Default country code (Ghana)
 */
export const DEFAULT_COUNTRY_CODE = '+233';

/**
 * Normalizes a phone number by removing all non-digit characters.
 */
export function normalizePhoneNumber(phone: string): string {
  return phone.replace(/\D/g, '');
}

/**
 * Formats a phone number with country code.
 * Handles various input formats:
 * - Numbers starting with country code (e.g., 233500603563, +233500603563)
 * - Numbers starting with 0 (e.g., 0500603563 -> +233500603563)
 * - Numbers without prefix (e.g., 500603563 -> +233500603563)
 * 
 * @param phone - The phone number to format
 * @param countryCode - The country code to use (e.g., '+233')
 * @returns Formatted phone number with country code (e.g., '+233500603563')
 */
export function formatPhoneNumberWithCountryCode(
  phone: string,
  countryCode: string = DEFAULT_COUNTRY_CODE
): string {
  if (!phone) return '';

  // Remove all non-digit characters except +
  const normalized = phone.replace(/[^\d+]/g, '');
  
  if (!normalized) return '';

  // Remove leading + if present in country code
  const cleanCountryCode = countryCode.replace(/^\+/, '');
  
  // Get digits only (without +) for comparison
  const digitsOnly = normalized.replace(/\+/g, '');
  
  // Check if number already starts with country code (with or without +)
  if (digitsOnly.startsWith(cleanCountryCode)) {
    // Already has country code, just ensure it starts with +
    return `+${digitsOnly}`;
  }

  // Check if it's a double country code (e.g., +233+233... or 233233...)
  if (digitsOnly.startsWith(cleanCountryCode + cleanCountryCode)) {
    // Remove duplicate country code
    return `+${digitsOnly.slice(cleanCountryCode.length)}`;
  }

  // Check if number starts with 0 (common in Ghana and other countries)
  // Remove leading 0 and add country code
  if (digitsOnly.startsWith('0')) {
    return `+${cleanCountryCode}${digitsOnly.slice(1)}`;
  }

  // Check if it's already a full international number (starts with another country code)
  const hasInternationalPrefix = digitsOnly.length > 10 && 
    COUNTRY_CODES.some(cc => {
      const ccDigits = cc.dialCode.replace(/^\+/, '');
      return digitsOnly.startsWith(ccDigits) && ccDigits !== cleanCountryCode;
    });
  
  if (hasInternationalPrefix) {
    return `+${digitsOnly}`;
  }

  // Add country code prefix
  return `+${cleanCountryCode}${digitsOnly}`;
}

/**
 * Validates if a phone number is in a valid format.
 * 
 * @param phone - The phone number to validate
 * @returns True if the phone number is valid
 */
export function isValidPhoneNumber(phone: string): boolean {
  if (!phone) return false;
  
  // Remove all non-digit characters except +
  const normalized = phone.replace(/[^\d+]/g, '');
  
  // Must start with + and have 10-15 digits after country code
  if (!normalized.startsWith('+')) return false;
  
  const digitsAfterPlus = normalized.slice(1);
  return /^\d{10,15}$/.test(digitsAfterPlus);
}

/**
 * Detects the country code from a phone number if possible.
 * 
 * @param phone - The phone number to analyze
 * @returns The detected country code or null
 */
export function detectCountryCode(phone: string): string | null {
  if (!phone) return null;
  
  const normalized = normalizePhoneNumber(phone);
  
  // Check if number starts with any known country code
  for (const country of COUNTRY_CODES) {
    const dialCodeDigits = country.dialCode.replace(/^\+/, '');
    if (normalized.startsWith(dialCodeDigits)) {
      return country.dialCode;
    }
  }
  
  return null;
}

/**
 * Gets country code info by dial code.
 */
export function getCountryByDialCode(dialCode: string): CountryCode | null {
  return COUNTRY_CODES.find(cc => cc.dialCode === dialCode) || null;
}

