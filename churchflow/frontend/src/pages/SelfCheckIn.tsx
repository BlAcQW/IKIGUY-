/**
 * Self-Service Check-In Page
 *
 * Public page for attendees to check themselves in by scanning their QR code.
 * Automatically performs check-in and plays voice greeting.
 *
 * URL: /self-checkin?code=REG-XXX
 */

import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, Loader, QrCode, User, Calendar, MapPin } from 'lucide-react';
import GreetingAudioPlayer from '../components/GreetingAudioPlayer';
import type { GreetingAudio } from '../lib/api';

interface CheckInResponse {
  id: string;
  user_name: string;
  user_phone: string;
  user_email?: string;
  conference_name: string;
  conference_id: string;
  checked_in_at: string;
  branch_name?: string;
  greeting_audio?: GreetingAudio;
  is_repeat_checkin?: boolean;
}

export default function SelfCheckIn() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [checkInData, setCheckInData] = useState<CheckInResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [greetingPlayed, setGreetingPlayed] = useState(false);
  const [gettingLocation, setGettingLocation] = useState(false);
  const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);

  const registrationCode = searchParams.get('code');

  useEffect(() => {
    if (!registrationCode) {
      // Redirect to /members page for manual check-in when no code provided
      navigate('/members', { replace: true });
      return;
    }

    // Get user's location first, then perform check-in
    getUserLocation();
  }, [registrationCode, navigate]);

  const getUserLocation = () => {
    if (!navigator.geolocation) {
      // Geolocation not supported - proceed without location
      setLocationError('Location services not supported by your browser');
      performCheckIn(null, null);
      return;
    }

    setGettingLocation(true);

    navigator.geolocation.getCurrentPosition(
      // Success callback
      (position) => {
        const { latitude, longitude } = position.coords;
        setUserLocation({ latitude, longitude });
        setGettingLocation(false);
        performCheckIn(latitude, longitude);
      },
      // Error callback
      (error) => {
        let errorMessage = 'Unable to get your location';

        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMessage = 'Location permission denied. Check-in without location verification...';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMessage = 'Location information unavailable';
            break;
          case error.TIMEOUT:
            errorMessage = 'Location request timed out';
            break;
        }

        setLocationError(errorMessage);
        setGettingLocation(false);

        // Proceed with check-in without location
        // Backend will validate if location is required
        performCheckIn(null, null);
      },
      // Options
      {
        enableHighAccuracy: true,
        timeout: 10000, // 10 seconds
        maximumAge: 0 // Don't use cached position
      }
    );
  };

  const performCheckIn = async (latitude: number | null, longitude: number | null) => {
    if (!registrationCode) return;

    try {
      setLoading(true);
      setError(null);

      const requestBody: any = {
        registration_code: registrationCode,
        is_self_checkin: true  // Flag to indicate self-service check-in
      };

      // Include location if available
      if (latitude !== null && longitude !== null) {
        requestBody.latitude = latitude;
        requestBody.longitude = longitude;
      }

      const response = await fetch(`/api/v1/registrations/check-in`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (response.ok) {
        setCheckInData(data);
      } else {
        // Handle specific error cases
        if (response.status === 403) {
          setError('Self-service check-in is currently disabled for this event. Please check in with event staff at the registration desk.');
        } else if (response.status === 404) {
          setError('Registration not found. Please verify your QR code.');
        } else {
          setError(data.detail || 'Check-in failed. Please try again or contact support.');
        }
      }
    } catch (err: any) {
      console.error('Check-in error:', err);
      setError('Unable to connect to server. Please check your internet connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleGreetingComplete = () => {
    setGreetingPlayed(true);
  };

  const handleTryAgain = () => {
    navigate('/self-checkin');
    window.location.reload();
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-600 mx-auto mb-6"></div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Checking you in...</h2>
          <p className="text-gray-600">Please wait while we process your registration</p>
          <div className="mt-6 space-y-3">
            {gettingLocation && (
              <div className="flex items-center justify-center space-x-2">
                <MapPin className="w-5 h-5 text-blue-600 animate-pulse" />
                <span className="text-sm text-gray-600">Getting your location...</span>
              </div>
            )}
            {locationError && (
              <div className="flex items-center justify-center space-x-2">
                <span className="text-xs text-amber-600">{locationError}</span>
              </div>
            )}
            <div className="flex items-center justify-center space-x-2">
              <Loader className="w-5 h-5 text-purple-600 animate-pulse" />
              <span className="text-sm text-gray-500">
                {gettingLocation ? 'Waiting for location...' : 'Processing check-in...'}
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 via-orange-50 to-yellow-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-red-100 rounded-full mb-4">
              <XCircle className="w-12 h-12 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Check-In Failed</h2>
            <p className="text-gray-700 mb-6">{error}</p>
          </div>

          <div className="space-y-3">
            <button
              onClick={handleTryAgain}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => navigate('/')}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-3 px-4 rounded-lg transition-colors"
            >
              Return Home
            </button>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Need help?</strong> Please contact the registration desk or event staff for assistance.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Success state
  if (checkInData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
          {/* Success Header */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-4 animate-bounce">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {checkInData.is_repeat_checkin ? 'Welcome Back!' : 'Welcome!'}
            </h1>
            <p className="text-lg text-gray-700">
              {checkInData.is_repeat_checkin
                ? "You're already checked in. Have a great time!"
                : "You're successfully checked in"}
            </p>
          </div>

          {/* User Details */}
          <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 mb-6 border border-purple-200">
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <User className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-gray-600">Name</p>
                  <p className="text-lg font-semibold text-gray-900">{checkInData.user_name}</p>
                  {checkInData.user_email && (
                    <p className="text-sm text-gray-600 mt-1">{checkInData.user_email}</p>
                  )}
                </div>
              </div>

              <div className="flex items-start space-x-3">
                <Calendar className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-gray-600">Event</p>
                  <p className="text-lg font-semibold text-gray-900">{checkInData.conference_name}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {new Date(checkInData.checked_in_at).toLocaleString('en-US', {
                      weekday: 'long',
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
              </div>

              {checkInData.branch_name && (
                <div className="flex items-start space-x-3">
                  <MapPin className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-gray-600">Branch</p>
                    <p className="text-lg font-semibold text-gray-900">{checkInData.branch_name}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Voice Greeting */}
          {checkInData.greeting_audio && (
            <div className="mb-6">
              <GreetingAudioPlayer
                greetingAudio={checkInData.greeting_audio}
                autoPlay={true}
                onPlaybackComplete={handleGreetingComplete}
              />
            </div>
          )}

          {/* Instructions */}
          <div className="bg-blue-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-blue-900 font-medium mb-2">What's Next?</p>
            <ul className="space-y-2 text-sm text-blue-800">
              <li className="flex items-start">
                <span className="mr-2">✓</span>
                <span>Proceed to the event venue</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">✓</span>
                <span>Show this confirmation to event staff if needed</span>
              </li>
              <li className="flex items-start">
                <span className="mr-2">✓</span>
                <span>Enjoy the event!</span>
              </li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={() => navigate('/')}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
            >
              Return Home
            </button>
          </div>

          {/* Fallback indicator (if using pre-recorded audio) */}
          {checkInData.greeting_audio?.is_fallback && (
            <div className="mt-4 text-center">
              <p className="text-xs text-gray-500">
                Using standard welcome greeting
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Fallback (should not reach here)
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center">
        <QrCode className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Ready to Check In?</h2>
        <p className="text-gray-600 mb-6">Scan your QR code to get started</p>
        <button
          onClick={() => navigate('/')}
          className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
        >
          Go to Home
        </button>
      </div>
    </div>
  );
}
