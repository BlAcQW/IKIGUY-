/**
 * Auto Check-In Widget
 *
 * Floating notification that appears when user is near a branch with active service.
 * Provides one-tap check-in with distance display and dismissible UI.
 *
 * Features:
 * - Proximity detection using geolocation
 * - Active service detection
 * - One-tap check-in button
 * - Distance display with formatting
 * - Dismissible notification
 * - Animated entrance/exit
 * - Auto-hide after successful check-in
 */

import React, { useEffect, useState, useCallback } from 'react';
import { MapPin, X, Check, Loader2 } from 'lucide-react';
import { useGeolocation, formatDistance } from '../../hooks/useGeolocation';
import { API_BASE_URL } from '../../config/api-config';

interface NearbyBranch {
  branch_id: string;
  name: string;
  distance: number;
  active_service: {
    service_id: string;
    type: string;
    start_time: string;
    can_checkin: boolean;
  } | null;
}

interface AutoCheckinResponse {
  success: boolean;
  attendance_id: string;
  branch: string;
  service: string;
  distance: number;
  points_awarded: number;
  level_up: boolean;
  new_level?: number;
  badge_earned?: string;
  streak_updated: boolean;
  current_streak: number;
}

interface AutoCheckinWidgetProps {
  organizationId: string;
  userId: string;
  onCheckinSuccess?: (response: AutoCheckinResponse) => void;
}

export const AutoCheckinWidget: React.FC<AutoCheckinWidgetProps> = ({
  organizationId,
  userId,
  onCheckinSuccess
}) => {
  const [nearbyBranch, setNearbyBranch] = useState<NearbyBranch | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [isCheckingIn, setIsCheckingIn] = useState(false);
  const [checkinSuccess, setCheckinSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    latitude,
    longitude,
    accuracy,
    error: geoError,
    loading: geoLoading,
    permissionStatus,
    requestLocation
  } = useGeolocation({
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 30000,
    watch: false
  });

  /**
   * Check for nearby branches when location is available
   */
  const checkNearbyBranches = useCallback(async () => {
    if (!latitude || !longitude) return;

    try {
      const response = await fetch(`${API_BASE_URL}/proximity-checkin/nearby-branches`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          latitude,
          longitude,
          organization_id: organizationId
        })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch nearby branches');
      }

      const data = await response.json();

      if (data.branches && data.branches.length > 0) {
        const branch = data.branches[0];

        // Only show if within 1km and has active service
        if (branch.distance <= 1000 && branch.active_service?.can_checkin) {
          setNearbyBranch(branch);
          setIsVisible(true);
        } else {
          setNearbyBranch(null);
          setIsVisible(false);
        }
      } else {
        setNearbyBranch(null);
        setIsVisible(false);
      }
    } catch (error) {
      console.error('Error checking nearby branches:', error);
      setErrorMessage('Failed to check nearby branches');
    }
  }, [latitude, longitude, organizationId]);

  /**
   * Request location on mount and periodically (every 60 seconds)
   */
  useEffect(() => {
    if (permissionStatus === 'granted') {
      requestLocation();

      const interval = setInterval(() => {
        requestLocation();
      }, 60000); // Check every 60 seconds

      return () => clearInterval(interval);
    }
  }, [permissionStatus, requestLocation]);

  /**
   * Check for nearby branches when location updates
   */
  useEffect(() => {
    if (latitude && longitude && !geoLoading && !geoError) {
      checkNearbyBranches();
    }
  }, [latitude, longitude, geoLoading, geoError, checkNearbyBranches]);

  /**
   * Handle auto check-in
   */
  const handleCheckin = async () => {
    if (!nearbyBranch || !latitude || !longitude || !accuracy) return;

    setIsCheckingIn(true);
    setErrorMessage(null);

    try {
      const response = await fetch(`${API_BASE_URL}/proximity-checkin/auto-checkin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          latitude,
          longitude,
          accuracy,
          branch_id: nearbyBranch.branch_id,
          service_id: nearbyBranch.active_service?.service_id,
          organization_id: organizationId
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Check-in failed');
      }

      const data: AutoCheckinResponse = await response.json();

      // Show success state
      setCheckinSuccess(true);

      // Call success callback
      if (onCheckinSuccess) {
        onCheckinSuccess(data);
      }

      // Auto-hide after 3 seconds
      setTimeout(() => {
        setIsVisible(false);
        setCheckinSuccess(false);
        setNearbyBranch(null);
      }, 3000);

    } catch (error) {
      console.error('Check-in error:', error);
      setErrorMessage(error instanceof Error ? error.message : 'Check-in failed');
    } finally {
      setIsCheckingIn(false);
    }
  };

  /**
   * Dismiss notification
   */
  const handleDismiss = () => {
    setIsVisible(false);
    setTimeout(() => {
      setNearbyBranch(null);
      setCheckinSuccess(false);
      setErrorMessage(null);
    }, 300); // Wait for animation
  };

  /**
   * Request permission if denied
   */
  const handleRequestPermission = () => {
    requestLocation();
  };

  // Don't render if not visible
  if (!isVisible || !nearbyBranch) {
    return null;
  }

  // Success state
  if (checkinSuccess) {
    return (
      <div className="fixed bottom-24 left-4 right-4 md:left-auto md:right-4 md:w-96
                      bg-green-600 text-white rounded-lg shadow-2xl p-4
                      animate-slide-up z-50 transition-all duration-300">
        <div className="flex items-center space-x-3">
          <div className="bg-white rounded-full p-2">
            <Check className="h-6 w-6 text-green-600" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold">Checked In Successfully!</h3>
            <p className="text-sm text-green-100">
              {nearbyBranch.name} • {nearbyBranch.active_service?.type}
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Permission denied state
  if (permissionStatus === 'denied') {
    return (
      <div className="fixed bottom-24 left-4 right-4 md:left-auto md:right-4 md:w-96
                      bg-orange-600 text-white rounded-lg shadow-2xl p-4
                      animate-slide-up z-50">
        <div className="flex items-start space-x-3">
          <MapPin className="h-6 w-6 mt-1" />
          <div className="flex-1">
            <h3 className="font-semibold">Location Permission Required</h3>
            <p className="text-sm text-orange-100 mb-3">
              Enable location access to use auto check-in
            </p>
            <button
              onClick={handleRequestPermission}
              className="w-full bg-white text-orange-600 rounded-lg py-2 font-semibold
                         hover:bg-orange-50 transition-colors"
            >
              Enable Location
            </button>
          </div>
          <button onClick={handleDismiss} className="hover:bg-orange-700 rounded p-1">
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>
    );
  }

  // Error state
  if (errorMessage) {
    return (
      <div className="fixed bottom-24 left-4 right-4 md:left-auto md:right-4 md:w-96
                      bg-red-600 text-white rounded-lg shadow-2xl p-4
                      animate-slide-up z-50">
        <div className="flex items-start space-x-3">
          <X className="h-6 w-6 mt-1" />
          <div className="flex-1">
            <h3 className="font-semibold">Check-In Failed</h3>
            <p className="text-sm text-red-100">{errorMessage}</p>
          </div>
          <button onClick={handleDismiss} className="hover:bg-red-700 rounded p-1">
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>
    );
  }

  // Main check-in widget
  return (
    <div className="fixed bottom-24 left-4 right-4 md:left-auto md:right-4 md:w-96
                    bg-purple-600 text-white rounded-lg shadow-2xl p-4
                    animate-slide-up z-50 transition-all duration-300">
      <div className="flex items-start space-x-3">
        <div className="bg-purple-500 rounded-full p-2">
          <MapPin className="h-6 w-6" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold">You're near {nearbyBranch.name}</h3>
          <p className="text-sm text-purple-100 mb-3">
            {formatDistance(nearbyBranch.distance)} away • {nearbyBranch.active_service?.type}
          </p>
          <button
            onClick={handleCheckin}
            disabled={isCheckingIn}
            className="w-full bg-white text-purple-600 rounded-lg py-2 font-semibold
                       hover:bg-purple-50 transition-colors disabled:opacity-50
                       disabled:cursor-not-allowed flex items-center justify-center
                       space-x-2"
          >
            {isCheckingIn ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Checking In...</span>
              </>
            ) : (
              <span>Check In Now</span>
            )}
          </button>
        </div>
        <button
          onClick={handleDismiss}
          disabled={isCheckingIn}
          className="hover:bg-purple-700 rounded p-1 disabled:opacity-50"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
};

export default AutoCheckinWidget;
