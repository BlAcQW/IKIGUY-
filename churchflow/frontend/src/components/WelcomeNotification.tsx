/**
 * Welcome Notification Component
 * 
 * Shows a geolocation-based welcome notification when a registered user
 * or PWA user arrives at a church branch location.
 * 
 * How it works:
 * 1. Checks location once when page loads (if permission granted)
 * 2. Periodically checks location every 2 minutes while the app is active
 * 3. When location is detected, queries nearby branches API
 * 4. Shows welcome notification if within 1km of a branch
 * 5. Prevents duplicate notifications with 1-hour cooldown per branch
 * 
 * Battery optimization:
 * - Uses cached location (maximumAge: 60 seconds) to reduce GPS usage
 * - Only checks when app is active (not in background)
 * - Uses 2-minute intervals (not continuous tracking)
 */

import { useEffect, useState, useCallback } from 'react';
import { MapPin, X, Church } from 'lucide-react';
import { useGeolocation } from '../hooks/useGeolocation';
import { isAuthenticated } from '../lib/auth-utils';
import { usePWA } from '../hooks/usePWA';
import { API_BASE_URL } from '../config/api-config';

interface NearbyBranch {
  branch_id: string;
  name: string;
  location: string;
  distance: number;
}

interface UserProfile {
  id: string;
  name: string;
  phone?: string;
  email?: string;
}

const STORAGE_KEY_PREFIX = 'churchflow_welcome_notified_';
const NOTIFICATION_COOLDOWN_MS = 3600000; // 1 hour cooldown between notifications for same branch
const MAX_DISTANCE_METERS = 1000; // Show notification if within 1km of branch

export default function WelcomeNotification() {
  const [isAuthenticatedUser, setIsAuthenticatedUser] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [nearbyBranch, setNearbyBranch] = useState<NearbyBranch | null>(null);
  const [showNotification, setShowNotification] = useState(false);
  const [organizationId, setOrganizationId] = useState<string | null>(null);
  const { isInstalled } = usePWA();

  const {
    latitude,
    longitude,
    error: geoError,
    loading: geoLoading,
    permissionStatus,
    requestLocation
  } = useGeolocation({
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 60000, // Cache location for 1 minute
    watch: false
  });

  /**
   * Check if user is authenticated and fetch profile
   */
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const authenticated = await isAuthenticated();
        setIsAuthenticatedUser(authenticated);

        if (authenticated) {
          // Fetch user profile
          const token = localStorage.getItem('access_token');
          const orgId = localStorage.getItem('current_organization_id');
          
          if (orgId) {
            setOrganizationId(orgId);
          }

          if (token) {
            try {
              const response = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
              });

              if (response.ok) {
                const userData = await response.json();
                setUserProfile({
                  id: userData.id,
                  name: userData.name || 'User',
                  phone: userData.phone,
                  email: userData.email
                });

                // Get organization ID from user data if available
                if (userData.organization_id) {
                  setOrganizationId(userData.organization_id);
                }
              }
            } catch (error) {
              console.error('Failed to fetch user profile:', error);
            }
          }
        }
      } catch (error) {
        console.error('Failed to check authentication:', error);
      }
    };

    checkAuth();
  }, []);

  /**
   * Check if we've already shown a notification for this branch recently
   */
  const hasRecentNotification = useCallback((branchId: string): boolean => {
    const storageKey = `${STORAGE_KEY_PREFIX}${branchId}`;
    const lastNotified = localStorage.getItem(storageKey);
    
    if (!lastNotified) {
      return false;
    }

    const lastNotifiedTime = parseInt(lastNotified, 10);
    const now = Date.now();
    const timeSinceNotification = now - lastNotifiedTime;

    return timeSinceNotification < NOTIFICATION_COOLDOWN_MS;
  }, []);

  /**
   * Mark that we've shown a notification for this branch
   */
  const markAsNotified = useCallback((branchId: string) => {
    const storageKey = `${STORAGE_KEY_PREFIX}${branchId}`;
    localStorage.setItem(storageKey, Date.now().toString());
  }, []);

  /**
   * Get organization ID - from user profile, localStorage, or default
   */
  const getOrganizationId = useCallback(async (): Promise<string | null> => {
    // If authenticated, use organization from profile or localStorage
    if (isAuthenticatedUser && organizationId) {
      return organizationId;
    }

    // For unauthenticated users, try to get from localStorage
    const storedOrgId = localStorage.getItem('current_organization_id');
    if (storedOrgId) {
      return storedOrgId;
    }

    // For unauthenticated PWA users, we'll need to use a default organization
    // This could be set via environment variable or use the first active organization
    // For now, return null and let the API handle it with get_optional_organization_id
    return null;
  }, [isAuthenticatedUser, organizationId]);

  /**
   * Find nearby branches and show notification if within range
   */
  const checkNearbyBranches = useCallback(async () => {
    if (!latitude || !longitude) {
      return;
    }

    // Only proceed if user is authenticated OR app is installed (PWA)
    if (!isAuthenticatedUser && !isInstalled) {
      return;
    }

    try {
      const orgId = await getOrganizationId();
      
      // Use public endpoint for unauthenticated users, authenticated endpoint for logged-in users
      const endpoint = isAuthenticatedUser 
        ? `${API_BASE_URL}/proximity-checkin/nearby-branches`
        : `${API_BASE_URL}/proximity-checkin/nearby-branches/public`;

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      // Add auth token if authenticated
      if (isAuthenticatedUser) {
        const token = localStorage.getItem('access_token');
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      // Add organization ID header if available (for public endpoint)
      if (orgId) {
        headers['X-Organization-ID'] = orgId;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          latitude,
          longitude,
          organization_id: orgId || '', // Required for authenticated, optional for public
          max_distance: MAX_DISTANCE_METERS,
          auto_checkin_only: false // Check all branches
        })
      });

      if (!response.ok) {
        console.error('Failed to fetch nearby branches:', response.statusText);
        return;
      }

      const branches: NearbyBranch[] = await response.json();

      if (branches && branches.length > 0) {
        const nearestBranch = branches[0];

        // Check if we've already shown notification for this branch recently
        if (!hasRecentNotification(nearestBranch.branch_id)) {
          setNearbyBranch(nearestBranch);
          setShowNotification(true);
          markAsNotified(nearestBranch.branch_id);
        }
      }
    } catch (error) {
      console.error('Error checking nearby branches:', error);
    }
  }, [latitude, longitude, isAuthenticatedUser, isInstalled, getOrganizationId, hasRecentNotification, markAsNotified]);

  /**
   * Request location when (authenticated OR PWA installed) and permission is granted
   * Also set up periodic checking every 2 minutes to detect when user arrives at church
   */
  useEffect(() => {
    if ((isAuthenticatedUser || isInstalled) && permissionStatus === 'granted') {
      // Initial location request
      requestLocation();

      // Set up periodic checking every 2 minutes (120000ms)
      // This allows us to detect when a user arrives at church after the page has loaded
      const intervalId = setInterval(() => {
        requestLocation();
      }, 120000); // Check every 2 minutes

      return () => {
        clearInterval(intervalId);
      };
    }
  }, [isAuthenticatedUser, isInstalled, permissionStatus, requestLocation]);

  /**
   * Check for nearby branches when location is available
   */
  useEffect(() => {
    if (latitude && longitude && !geoLoading && !geoError && (isAuthenticatedUser || isInstalled)) {
      checkNearbyBranches();
    }
  }, [latitude, longitude, geoLoading, geoError, isAuthenticatedUser, isInstalled, checkNearbyBranches]);

  /**
   * Auto-hide notification after 8 seconds
   */
  useEffect(() => {
    if (showNotification) {
      const timer = setTimeout(() => {
        setShowNotification(false);
      }, 8000);

      return () => clearTimeout(timer);
    }
  }, [showNotification]);

  // Don't render if not authenticated and not PWA installed
  if ((!isAuthenticatedUser && !isInstalled) || !showNotification || !nearbyBranch) {
    return null;
  }

  // For authenticated users, use their name; for unauthenticated, use generic greeting
  const userName = isAuthenticatedUser && userProfile 
    ? userProfile.name.split(' ')[0] || 'there'
    : null;

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in-right max-w-sm w-full">
      <div className="bg-gradient-to-r from-purple-600 via-purple-700 to-blue-700 text-white rounded-2xl shadow-2xl p-6 border-2 border-white/20">
        {/* Close button */}
        <button
          onClick={() => setShowNotification(false)}
          className="absolute top-3 right-3 p-1.5 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-all"
          aria-label="Close notification"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Content */}
        <div className="flex items-start gap-4 pr-8">
          {/* Icon */}
          <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center ring-4 ring-white/20 flex-shrink-0">
            <Church className="w-6 h-6 text-white" />
          </div>

          {/* Text */}
          <div className="flex-1">
            <h3 className="text-lg font-bold mb-1">
              {userName ? `Hello ${userName}, welcome to church!` : 'Welcome to church!'}
            </h3>
            <p className="text-white/90 text-sm mb-3">
              You're at <span className="font-semibold">{nearbyBranch.name}</span>
            </p>
            <div className="flex items-center gap-2 text-white/80 text-xs">
              <MapPin className="w-3.5 h-3.5" />
              <span>
                {nearbyBranch.distance < 1000
                  ? `${Math.round(nearbyBranch.distance)}m away`
                  : `${(nearbyBranch.distance / 1000).toFixed(1)}km away`}
              </span>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slide-in-right {
          from {
            opacity: 0;
            transform: translateX(100%);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        .animate-slide-in-right {
          animation: slide-in-right 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}

