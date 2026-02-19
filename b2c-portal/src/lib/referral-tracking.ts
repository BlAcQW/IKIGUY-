/**
 * Referral Tracking Utility
 *
 * Handles cookie-based referral attribution with 30-day expiration.
 * Follows industry standards for affiliate tracking:
 * - First-click attribution model
 * - Secure cookie storage
 * - Device fingerprinting
 * - UTM parameter tracking
 */

import Cookies from 'js-cookie';
import { affiliateApi } from './core-api';

// Cookie configuration
const REFERRAL_COOKIE_NAME = 'kasaai_ref';
const REFERRAL_EXPIRY_DAYS = 30;
const UTM_COOKIE_NAME = 'kasaai_utm';
const DEVICE_FP_COOKIE_NAME = 'kasaai_device_fp';

/**
 * UTM Parameters for campaign tracking
 */
export interface UTMParams {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
}

/**
 * Referral data stored in cookies
 */
export interface ReferralData {
  referral_code: string;
  timestamp: number;
  utm_params?: UTMParams;
  landing_page: string;
}

/**
 * Device fingerprint for tracking
 */
interface DeviceFingerprint {
  user_agent: string;
  screen_resolution: string;
  timezone: string;
  language: string;
  platform: string;
}

/**
 * Generate a simple device fingerprint
 * Note: This is basic. For production, consider using FingerprintJS or similar
 */
function generateDeviceFingerprint(): DeviceFingerprint {
  return {
    user_agent: navigator.userAgent,
    screen_resolution: `${window.screen.width}x${window.screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language,
    platform: navigator.platform
  };
}

/**
 * Get or create device fingerprint cookie
 */
function getDeviceFingerprint(): string {
  let fingerprint = Cookies.get(DEVICE_FP_COOKIE_NAME);

  if (!fingerprint) {
    const fp = generateDeviceFingerprint();
    fingerprint = btoa(JSON.stringify(fp)); // Base64 encode

    // Store for 1 year
    Cookies.set(DEVICE_FP_COOKIE_NAME, fingerprint, {
      expires: 365,
      sameSite: 'Lax',
      secure: window.location.protocol === 'https:'
    });
  }

  return fingerprint;
}

/**
 * Extract UTM parameters from URL
 */
function extractUTMParams(searchParams: URLSearchParams): UTMParams | undefined {
  const utmParams: UTMParams = {};
  let hasUTM = false;

  const utmKeys: (keyof UTMParams)[] = [
    'utm_source',
    'utm_medium',
    'utm_campaign',
    'utm_term',
    'utm_content'
  ];

  utmKeys.forEach(key => {
    const value = searchParams.get(key);
    if (value) {
      utmParams[key] = value;
      hasUTM = true;
    }
  });

  return hasUTM ? utmParams : undefined;
}

/**
 * Store referral data in cookie and localStorage (backup)
 */
function storeReferralData(referralCode: string, utmParams?: UTMParams): void {
  const referralData: ReferralData = {
    referral_code: referralCode.toUpperCase(),
    timestamp: Date.now(),
    utm_params: utmParams,
    landing_page: window.location.pathname
  };

  // Primary storage: Cookie
  Cookies.set(REFERRAL_COOKIE_NAME, JSON.stringify(referralData), {
    expires: REFERRAL_EXPIRY_DAYS,
    sameSite: 'Lax',
    secure: window.location.protocol === 'https:'
  });

  // Backup storage: LocalStorage (survives cookie clearing)
  try {
    localStorage.setItem(REFERRAL_COOKIE_NAME, JSON.stringify(referralData));
  } catch (error) {
    console.warn('[Referral Tracking] Failed to store in localStorage:', error);
    // Continue - cookie storage is primary
  }

  // Store UTM params separately for easier access
  if (utmParams) {
    Cookies.set(UTM_COOKIE_NAME, JSON.stringify(utmParams), {
      expires: REFERRAL_EXPIRY_DAYS,
      sameSite: 'Lax',
      secure: window.location.protocol === 'https:'
    });
    
    // Also backup UTM in localStorage
    try {
      localStorage.setItem(UTM_COOKIE_NAME, JSON.stringify(utmParams));
    } catch (error) {
      // Ignore localStorage errors for UTM
    }
  }

  console.log('[Referral Tracking] Stored referral:', {
    code: referralCode,
    utm: utmParams,
    page: window.location.pathname
  });
}

/**
 * Get stored referral data from cookie or localStorage (backup)
 */
export function getReferralData(): ReferralData | null {
  // Priority 1: Try cookie (primary storage)
  let cookieValue = Cookies.get(REFERRAL_COOKIE_NAME);
  let storageSource = 'cookie';

  // Priority 2: Fallback to localStorage if cookie not available
  if (!cookieValue) {
    try {
      cookieValue = localStorage.getItem(REFERRAL_COOKIE_NAME);
      storageSource = 'localStorage';
    } catch (error) {
      console.warn('[Referral Tracking] Failed to read from localStorage:', error);
    }
  }

  if (!cookieValue) {
    return null;
  }

  try {
    const data = JSON.parse(cookieValue) as ReferralData;

    // Check if expired (30 days)
    const expiryTime = data.timestamp + (REFERRAL_EXPIRY_DAYS * 24 * 60 * 60 * 1000);
    if (Date.now() > expiryTime) {
      clearReferralData();
      return null;
    }

    // If we got it from localStorage but cookie is missing, restore to cookie
    if (storageSource === 'localStorage' && !Cookies.get(REFERRAL_COOKIE_NAME)) {
      try {
        Cookies.set(REFERRAL_COOKIE_NAME, cookieValue, {
          expires: REFERRAL_EXPIRY_DAYS,
          sameSite: 'Lax',
          secure: window.location.protocol === 'https:'
        });
        console.log('[Referral Tracking] Restored referral code from localStorage to cookie');
      } catch (error) {
        // Ignore cookie restoration errors
      }
    }

    return data;
  } catch (error) {
    console.error('[Referral Tracking] Error parsing referral data:', error);
    return null;
  }
}

/**
 * Get referral code from cookie (convenience method)
 */
export function getReferralCode(): string | null {
  const data = getReferralData();
  return data ? data.referral_code : null;
}

/**
 * Get UTM parameters from cookie
 */
export function getUTMParams(): UTMParams | null {
  const cookieValue = Cookies.get(UTM_COOKIE_NAME);

  if (!cookieValue) {
    return null;
  }

  try {
    return JSON.parse(cookieValue) as UTMParams;
  } catch (error) {
    console.error('[Referral Tracking] Error parsing UTM cookie:', error);
    return null;
  }
}

/**
 * Clear referral data (e.g., after successful attribution)
 */
export function clearReferralData(): void {
  // Clear from cookie
  Cookies.remove(REFERRAL_COOKIE_NAME);
  Cookies.remove(UTM_COOKIE_NAME);
  
  // Also clear from localStorage backup
  try {
    localStorage.removeItem(REFERRAL_COOKIE_NAME);
    localStorage.removeItem(UTM_COOKIE_NAME);
  } catch (error) {
    console.warn('[Referral Tracking] Failed to clear localStorage:', error);
  }
  
  console.log('[Referral Tracking] Cleared referral data');
}

/**
 * Track referral click and store in cookie
 * This should be called on every page load to check for ref parameter
 * 
 * If user clicks affiliate link, redirects to affiliate join page
 */
export async function trackReferralClick(): Promise<{ shouldRedirect: boolean; redirectPath?: string }> {
  try {
    const searchParams = new URLSearchParams(window.location.search);
    const refParam = searchParams.get('ref');

    // Priority 1: URL parameter (new referral overrides existing)
    if (refParam) {
      const utmParams = extractUTMParams(searchParams);

      // Track click on backend
      try {
        await affiliateApi.trackReferral(refParam.toUpperCase());
        console.log('[Referral Tracking] Click tracked for:', refParam);
      } catch (error) {
        console.error('[Referral Tracking] Failed to track click:', error);
        // Continue anyway - store in cookie for later attribution
      }

      // Store in cookie
      storeReferralData(refParam, utmParams);

      // Check if we should redirect to affiliate join page
      // Skip redirect if already on affiliate pages to avoid loops
      const currentPath = window.location.pathname;
      const isOnAffiliatePage = currentPath.includes('/affiliates/');

      if (!isOnAffiliatePage) {
        // Check authentication status (non-blocking)
        try {
          // Import mongoAuth dynamically to avoid circular dependencies
          const { mongoAuth } = await import('./mongo-auth');
          const isAuthenticated = mongoAuth.isAuthenticated();

          if (isAuthenticated) {
            // Check if user is already an affiliate
            try {
              await affiliateApi.getProfile();
              // User is already an affiliate - redirect to dashboard
              console.log('[Referral Tracking] User is already an affiliate, redirecting to dashboard');
              return {
                shouldRedirect: true,
                redirectPath: '/affiliates/dashboard'
              };
            } catch (error: any) {
              // If 404, user is not an affiliate - redirect to join page
              if (error.response?.status === 404) {
                console.log('[Referral Tracking] User not an affiliate, redirecting to join page');
                return {
                  shouldRedirect: true,
                  redirectPath: '/affiliates/join'
                };
              }
            }
          } else {
            // Not authenticated - redirect to join page (they can sign up there)
            console.log('[Referral Tracking] User not authenticated, redirecting to join page');
            return {
              shouldRedirect: true,
              redirectPath: '/affiliates/join'
            };
          }
        } catch (error) {
          // If auth check fails, still redirect to join page (safe default)
          console.log('[Referral Tracking] Auth check failed, redirecting to join page');
          return {
            shouldRedirect: true,
            redirectPath: '/affiliates/join'
          };
        }
      }

      // Clean URL (remove ref parameter) for better UX
      const cleanUrl = new URL(window.location.href);
      cleanUrl.searchParams.delete('ref');
      window.history.replaceState({}, '', cleanUrl.toString());

      return { shouldRedirect: false };
    }

    // Priority 2: Check if referral already stored in cookie
    const existingData = getReferralData();
    if (existingData) {
      console.log('[Referral Tracking] Existing referral found:', existingData.referral_code);
      return { shouldRedirect: false };
    }

    // No referral found
    console.log('[Referral Tracking] No referral detected');
    return { shouldRedirect: false };
  } catch (error) {
    console.error('[Referral Tracking] Error in trackReferralClick:', error);
    return { shouldRedirect: false };
  }
}

/**
 * Attribute signup to referral
 * This should be called after successful user signup
 */
export async function attributeSignup(userId: string, organizationId: string): Promise<boolean> {
  try {
    const referralData = getReferralData();

    if (!referralData) {
      console.log('[Referral Tracking] No referral to attribute');
      return false;
    }

    console.log('[Referral Tracking] Attributing signup to:', referralData.referral_code);

    // Call backend to attribute signup
    const attribution = await affiliateApi.attributeSignup(
      userId,
      organizationId,
      referralData.referral_code
    );

    if (attribution) {
      console.log('[Referral Tracking] Signup attributed successfully');

      // Clear referral data after successful attribution
      clearReferralData();

      return true;
    }

    return false;
  } catch (error) {
    console.error('[Referral Tracking] Failed to attribute signup:', error);
    return false;
  }
}

/**
 * Check if user came from a referral link
 */
export function hasReferral(): boolean {
  return getReferralCode() !== null;
}

/**
 * Get days remaining in referral attribution window
 */
export function getReferralDaysRemaining(): number | null {
  const data = getReferralData();

  if (!data) {
    return null;
  }

  const expiryTime = data.timestamp + (REFERRAL_EXPIRY_DAYS * 24 * 60 * 60 * 1000);
  const remainingMs = expiryTime - Date.now();
  const remainingDays = Math.ceil(remainingMs / (24 * 60 * 60 * 1000));

  return Math.max(0, remainingDays);
}

/**
 * Export for debugging purposes (development only)
 */
export const ReferralTracking = {
  trackClick: trackReferralClick,
  getReferralData,
  getReferralCode,
  getUTMParams,
  attributeSignup,
  clearReferralData,
  hasReferral,
  getDaysRemaining: getReferralDaysRemaining,

  // Debug methods
  debug: {
    getDeviceFingerprint,
    getAllCookies: () => ({
      referral: Cookies.get(REFERRAL_COOKIE_NAME),
      utm: Cookies.get(UTM_COOKIE_NAME),
      device_fp: Cookies.get(DEVICE_FP_COOKIE_NAME)
    })
  }
};

// Make available globally for debugging
if (typeof window !== 'undefined') {
  (window as any).ReferralTracking = ReferralTracking;
}
