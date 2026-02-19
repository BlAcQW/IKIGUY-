/**
 * useGeolocation Hook
 *
 * Battery-optimized location tracking with permission handling for
 * proximity-based auto check-in functionality.
 *
 * Features:
 * - Single position request or continuous watching
 * - Permission status tracking
 * - Error handling with user-friendly messages
 * - Battery optimization with debouncing
 * - Configurable accuracy and timeout
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export interface GeolocationState {
  latitude: number | null;
  longitude: number | null;
  accuracy: number | null;
  timestamp: number | null;
  error: string | null;
  loading: boolean;
  permissionStatus: 'prompt' | 'granted' | 'denied' | 'unsupported';
}

export interface GeolocationOptions {
  enableHighAccuracy?: boolean;
  timeout?: number;
  maximumAge?: number;
  watch?: boolean;
  onLocationUpdate?: (position: GeolocationPosition) => void;
  onError?: (error: string) => void;
}

const DEFAULT_OPTIONS: PositionOptions = {
  enableHighAccuracy: true,
  timeout: 10000, // 10 seconds
  maximumAge: 30000, // 30 seconds cache
};

/**
 * Custom hook for browser geolocation with battery optimization.
 *
 * @param options - Configuration options
 * @returns Geolocation state and control functions
 *
 * @example
 * ```tsx
 * const { latitude, longitude, error, requestLocation, permissionStatus } = useGeolocation({
 *   enableHighAccuracy: true,
 *   watch: false,
 * });
 *
 * // Request location once
 * <button onClick={requestLocation}>Get Location</button>
 * ```
 *
 * @example
 * ```tsx
 * // Continuous watching (for check-in mode)
 * const { latitude, longitude } = useGeolocation({
 *   watch: true,
 *   onLocationUpdate: (position) => {
 *     console.log('New position:', position.coords);
 *   }
 * });
 * ```
 */
export function useGeolocation(options: GeolocationOptions = {}): GeolocationState & {
  requestLocation: () => void;
  clearWatch: () => void;
  checkPermission: () => Promise<PermissionState | null>;
} {
  const [state, setState] = useState<GeolocationState>({
    latitude: null,
    longitude: null,
    accuracy: null,
    timestamp: null,
    error: null,
    loading: false,
    permissionStatus: 'prompt',
  });

  const watchIdRef = useRef<number | null>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Check if geolocation is supported
  const isSupported = 'geolocation' in navigator;

  /**
   * Check geolocation permission status
   */
  const checkPermission = useCallback(async (): Promise<PermissionState | null> => {
    if (!('permissions' in navigator)) {
      return null;
    }

    try {
      const result = await navigator.permissions.query({ name: 'geolocation' });
      setState((prev) => ({
        ...prev,
        permissionStatus: result.state as 'prompt' | 'granted' | 'denied',
      }));
      return result.state;
    } catch (error) {
      console.warn('Permission API not supported:', error);
      return null;
    }
  }, []);

  /**
   * Handle successful position retrieval
   */
  const handleSuccess = useCallback(
    (position: GeolocationPosition) => {
      const newState: GeolocationState = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        timestamp: position.timestamp,
        error: null,
        loading: false,
        permissionStatus: 'granted',
      };

      setState(newState);

      // Call optional callback
      if (options.onLocationUpdate) {
        options.onLocationUpdate(position);
      }
    },
    [options]
  );

  /**
   * Handle geolocation errors with user-friendly messages
   */
  const handleError = useCallback(
    (error: GeolocationPositionError) => {
      let errorMessage: string;

      switch (error.code) {
        case error.PERMISSION_DENIED:
          errorMessage = 'Location access denied. Please enable location permissions in your browser settings.';
          setState((prev) => ({ ...prev, permissionStatus: 'denied' }));
          break;
        case error.POSITION_UNAVAILABLE:
          errorMessage = 'Location information unavailable. Please check your device settings.';
          break;
        case error.TIMEOUT:
          errorMessage = 'Location request timed out. Please try again.';
          break;
        default:
          errorMessage = 'Unable to retrieve location. Please try again.';
      }

      setState((prev) => ({
        ...prev,
        error: errorMessage,
        loading: false,
      }));

      // Call optional error callback
      if (options.onError) {
        options.onError(errorMessage);
      }
    },
    [options]
  );

  /**
   * Request current position once
   */
  const requestLocation = useCallback(() => {
    if (!isSupported) {
      setState((prev) => ({
        ...prev,
        error: 'Geolocation is not supported by your browser.',
        permissionStatus: 'unsupported',
      }));
      return;
    }

    setState((prev) => ({ ...prev, loading: true, error: null }));

    const positionOptions: PositionOptions = {
      ...DEFAULT_OPTIONS,
      enableHighAccuracy: options.enableHighAccuracy ?? true,
      timeout: options.timeout ?? DEFAULT_OPTIONS.timeout,
      maximumAge: options.maximumAge ?? DEFAULT_OPTIONS.maximumAge,
    };

    navigator.geolocation.getCurrentPosition(
      handleSuccess,
      handleError,
      positionOptions
    );
  }, [isSupported, options, handleSuccess, handleError]);

  /**
   * Start watching position (continuous updates)
   */
  const startWatching = useCallback(() => {
    if (!isSupported) {
      setState((prev) => ({
        ...prev,
        error: 'Geolocation is not supported by your browser.',
        permissionStatus: 'unsupported',
      }));
      return;
    }

    setState((prev) => ({ ...prev, loading: true, error: null }));

    const positionOptions: PositionOptions = {
      ...DEFAULT_OPTIONS,
      enableHighAccuracy: options.enableHighAccuracy ?? true,
      timeout: options.timeout ?? DEFAULT_OPTIONS.timeout,
      maximumAge: options.maximumAge ?? DEFAULT_OPTIONS.maximumAge,
    };

    // Debounced success handler to reduce battery drain
    const debouncedSuccess = (position: GeolocationPosition) => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      debounceTimerRef.current = setTimeout(() => {
        handleSuccess(position);
      }, 1000); // 1 second debounce
    };

    watchIdRef.current = navigator.geolocation.watchPosition(
      debouncedSuccess,
      handleError,
      positionOptions
    );
  }, [isSupported, options, handleSuccess, handleError]);

  /**
   * Stop watching position
   */
  const clearWatch = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }

    setState((prev) => ({ ...prev, loading: false }));
  }, []);

  /**
   * Start watching on mount if watch option is enabled
   */
  useEffect(() => {
    if (options.watch) {
      startWatching();
    }

    // Check permission on mount
    checkPermission();

    return () => {
      clearWatch();
    };
  }, [options.watch, startWatching, clearWatch, checkPermission]);

  return {
    ...state,
    requestLocation,
    clearWatch,
    checkPermission,
  };
}

/**
 * Calculate distance between two GPS coordinates using Haversine formula.
 *
 * @param lat1 - First latitude
 * @param lon1 - First longitude
 * @param lat2 - Second latitude
 * @param lon2 - Second longitude
 * @returns Distance in meters
 *
 * @example
 * ```ts
 * const distance = calculateDistance(5.6037, -0.1870, 5.7108, -0.1673);
 * console.log(`Distance: ${distance.toFixed(0)} meters`);
 * ```
 */
export function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371000; // Earth's radius in meters
  const φ1 = (lat1 * Math.PI) / 180;
  const φ2 = (lat2 * Math.PI) / 180;
  const Δφ = ((lat2 - lat1) * Math.PI) / 180;
  const Δλ = ((lon2 - lon1) * Math.PI) / 180;

  const a =
    Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c; // Distance in meters
}

/**
 * Format distance for display.
 *
 * @param meters - Distance in meters
 * @returns Formatted string (e.g., "342m" or "1.2km")
 *
 * @example
 * ```ts
 * formatDistance(342); // "342m"
 * formatDistance(1234); // "1.2km"
 * ```
 */
export function formatDistance(meters: number): string {
  if (meters < 1000) {
    return `${Math.round(meters)}m`;
  }
  return `${(meters / 1000).toFixed(1)}km`;
}

/**
 * Check if user is within a certain radius of a location.
 *
 * @param userLat - User's latitude
 * @param userLon - User's longitude
 * @param targetLat - Target latitude
 * @param targetLon - Target longitude
 * @param radiusMeters - Radius in meters
 * @returns True if within radius
 *
 * @example
 * ```ts
 * const isNearby = isWithinRadius(5.6037, -0.1870, 5.7108, -0.1673, 5000);
 * console.log(isNearby ? 'Within range' : 'Too far');
 * ```
 */
export function isWithinRadius(
  userLat: number,
  userLon: number,
  targetLat: number,
  targetLon: number,
  radiusMeters: number
): boolean {
  const distance = calculateDistance(userLat, userLon, targetLat, targetLon);
  return distance <= radiusMeters;
}
