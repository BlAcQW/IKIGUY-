/**
 * Members Check-In Page
 *
 * Public page for church members to view their conference registration
 * and perform location-based self check-in.
 *
 * URL: /members
 */

import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  CheckCircle,
  XCircle,
  Loader,
  MapPin,
  Calendar,
  User,
  Phone,
  Mail,
  Church,
  Bus,
  AlertCircle,
  Navigation,
  Clock,
  List,
  QrCode,
  Camera,
  ArrowLeft,
} from 'lucide-react';
import CameraQRScanner from '../components/CameraQRScanner';
import { getApiUrl } from '../config';
import GreetingAudioPlayer from '../components/GreetingAudioPlayer';
import type { GreetingAudio } from '../lib/api';

interface TodaySession {
  id: string;
  name: string;
  description?: string;
  location?: string;
  day_number: number;
  day_label: string;
  order: number;
  session_date?: string;
  already_checked_in: boolean;
}

interface SessionLookupResponse {
  registration_id: string;
  user_name: string;
  user_phone: string;
  conference_id: string;
  conference_name: string;
  venue?: string;
  venue_latitude?: number;
  venue_longitude?: number;
  venue_checkin_radius?: number;
  location_checkin_required?: boolean;
  todays_sessions: TodaySession[];
}

interface PhoneRegistration {
  id: string;
  user_name: string;
  user_phone: string;
  conference_id: string;
  conference_name: string;
  registration_code: string;
  venue?: string;
  venue_latitude?: number;
  venue_longitude?: number;
  venue_checkin_radius?: number;
}

interface RegistrationData {
  id: string;
  user_name: string;
  user_phone: string;
  user_email?: string;
  conference_name: string;
  conference_id: string;
  conference_start_date?: string;
  conference_end_date?: string;
  venue?: string;
  venue_latitude?: number;
  venue_longitude?: number;
  venue_checkin_radius?: number;
  self_checkin_enabled: boolean;
  checked_in: boolean;
  checked_in_at?: string;
  branch_name?: string;
  church_name?: string;
  requires_bus: boolean;
  bus_route_name?: string;
  pickup_location?: string;
  special_needs?: string;
  registration_code: string;
  status: string;
}

interface CheckInResponse extends RegistrationData {
  greeting_audio?: GreetingAudio;
  is_repeat_checkin?: boolean;
}

export default function Members() {
  const navigate = useNavigate();

  // Tab state - default to session, conference tab hidden
  const [activeTab, setActiveTab] = useState<'conference' | 'session'>('session');

  // Form state
  const [registrationCode, setRegistrationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Registration data
  const [registration, setRegistration] = useState<RegistrationData | null>(null);

  // Location state
  const [userLocation, setUserLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [distance, setDistance] = useState<number | null>(null);
  const [checkingLocation, setCheckingLocation] = useState(false);

  // Check-in state
  const [checkingIn, setCheckingIn] = useState(false);
  const [checkInSuccess, setCheckInSuccess] = useState(false);
  const [checkInData, setCheckInData] = useState<CheckInResponse | null>(null);

  // Session check-in state
  const [sessionLookupMethod, setSessionLookupMethod] = useState<'qr' | 'code' | 'phone'>('qr');
  const [showQRScanner, setShowQRScanner] = useState(false);
  const [sessionCode, setSessionCode] = useState('');
  const [sessionPhone, setSessionPhone] = useState('');
  const [sessionLookupData, setSessionLookupData] = useState<SessionLookupResponse | null>(null);
  const [phoneRegistrations, setPhoneRegistrations] = useState<PhoneRegistration[]>([]);
  const [selectedPhoneReg, setSelectedPhoneReg] = useState<PhoneRegistration | null>(null);
  const [todaysSessions, setTodaysSessions] = useState<TodaySession[]>([]);
  const [selectedSession, setSelectedSession] = useState<TodaySession | null>(null);
  const [sessionCheckInSuccess, setSessionCheckInSuccess] = useState(false);
  const [sessionCheckInData, setSessionCheckInData] = useState<any>(null);
  const [sessionVenue, setSessionVenue] = useState<{
    latitude?: number;
    longitude?: number;
    radius?: number;
    locationRequired?: boolean;
  } | null>(null);

  // Track if user is not registered (to show registration prompt)
  const [showRegistrationPrompt, setShowRegistrationPrompt] = useState(false);

  // Calculate distance between two GPS coordinates using Haversine formula
  const calculateDistance = (
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ): number => {
    const R = 6371000; // Earth's radius in meters
    const lat1Rad = (lat1 * Math.PI) / 180;
    const lat2Rad = (lat2 * Math.PI) / 180;
    const deltaLat = ((lat2 - lat1) * Math.PI) / 180;
    const deltaLon = ((lon2 - lon1) * Math.PI) / 180;

    const a =
      Math.sin(deltaLat / 2) * Math.sin(deltaLat / 2) +
      Math.cos(lat1Rad) *
        Math.cos(lat2Rad) *
        Math.sin(deltaLon / 2) *
        Math.sin(deltaLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
  };

  // Get user's current location
  const getUserLocation = () => {
    setCheckingLocation(true);
    setLocationError(null);

    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser');
      setCheckingLocation(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const location = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        };
        setUserLocation(location);
        setCheckingLocation(false);

        // Calculate distance if registration has venue coordinates
        if (
          registration?.venue_latitude !== undefined &&
          registration?.venue_longitude !== undefined
        ) {
          const dist = calculateDistance(
            location.latitude,
            location.longitude,
            registration.venue_latitude,
            registration.venue_longitude
          );
          setDistance(dist);
        }
      },
      (error) => {
        let errorMsg = 'Unable to get your location';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMsg = 'Location permission denied. Please enable location access.';
            break;
          case error.POSITION_UNAVAILABLE:
            errorMsg = 'Location information unavailable';
            break;
          case error.TIMEOUT:
            errorMsg = 'Location request timed out';
            break;
        }
        setLocationError(errorMsg);
        setCheckingLocation(false);
      },
      {
        enableHighAccuracy: false, // Use network location first (faster)
        timeout: 30000, // 30 seconds timeout
        maximumAge: 60000, // Allow cached location up to 1 minute old
      }
    );
  };

  // Update distance when user location or registration changes
  useEffect(() => {
    if (
      userLocation &&
      registration?.venue_latitude !== undefined &&
      registration?.venue_longitude !== undefined
    ) {
      const dist = calculateDistance(
        userLocation.latitude,
        userLocation.longitude,
        registration.venue_latitude,
        registration.venue_longitude
      );
      setDistance(dist);
    }
  }, [userLocation, registration]);

  // Handle form submission to look up registration
  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!registrationCode.trim()) {
      setError('Please enter your registration code');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setRegistration(null);
      setUserLocation(null);
      setDistance(null);
      setCheckInSuccess(false);

      const response = await fetch(
        getApiUrl(`registrations/by-code/${registrationCode.trim()}`)
      );

      const data = await response.json();

      if (response.ok) {
        setRegistration(data);
        // Auto-get location if self check-in is enabled
        if (data.self_checkin_enabled && !data.checked_in) {
          getUserLocation();
        }
      } else {
        setError(data.detail || 'Registration not found');
      }
    } catch (err: any) {
      console.error('Lookup error:', err);
      setError('Unable to connect to server. Please check your internet connection.');
    } finally {
      setLoading(false);
    }
  };

  // Handle check-in
  const handleCheckIn = async () => {
    if (!registration || !userLocation) return;

    try {
      setCheckingIn(true);
      setError(null);

      const response = await fetch(getApiUrl('registrations/check-in'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          registration_code: registration.registration_code,
          is_self_checkin: true,
          latitude: userLocation.latitude,
          longitude: userLocation.longitude,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setCheckInSuccess(true);
        setCheckInData(data);
        setRegistration({ ...registration, checked_in: true, checked_in_at: data.checked_in_at });
      } else {
        if (response.status === 403) {
          // Could be location error or disabled check-in
          setError(data.detail || 'You are too far from the venue to check in.');
        } else if (response.status === 400) {
          setError(data.detail || 'Check-in failed. Please try again.');
        } else {
          setError(data.detail || 'Check-in failed. Please try again or contact support.');
        }
      }
    } catch (err: any) {
      console.error('Check-in error:', err);
      setError('Unable to connect to server. Please check your internet connection.');
    } finally {
      setCheckingIn(false);
    }
  };

  // Determine if check-in button should be enabled
  const isCheckInEnabled = (): boolean => {
    if (!registration || registration.checked_in) return false;
    if (!registration.self_checkin_enabled) return false;
    if (!userLocation || distance === null) return false;
    if (distance > (registration.venue_checkin_radius || 1000)) return false;
    return true;
  };

  // Format date
  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Reset form
  const handleReset = () => {
    setRegistrationCode('');
    setRegistration(null);
    setUserLocation(null);
    setDistance(null);
    setError(null);
    setCheckInSuccess(false);
    setCheckInData(null);
  };

  // Session check-in: lookup by code
  const handleSessionLookupByCode = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!sessionCode.trim()) {
      setError('Please enter your registration code');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSessionLookupData(null);
      setTodaysSessions([]);
      setSelectedSession(null);
      setShowRegistrationPrompt(false);

      const response = await fetch(
        getApiUrl(`member/sessions/today/${sessionCode.trim()}`)
      );

      const data = await response.json();

      if (response.ok) {
        setSessionLookupData(data);
        setTodaysSessions(data.todays_sessions || []);
        setSessionVenue({
          latitude: data.venue_latitude,
          longitude: data.venue_longitude,
          radius: data.venue_checkin_radius || 1000,
          locationRequired: data.location_checkin_required !== false,
        });
        // Auto-get location only if required
        if (data.location_checkin_required !== false) {
          getUserLocation();
        }
      } else {
        // Check if this is a "not found" error
        const errorMsg = data.detail || 'Failed to lookup registration';
        if (response.status === 404 || errorMsg.toLowerCase().includes('not found') || errorMsg.toLowerCase().includes('no registration')) {
          setShowRegistrationPrompt(true);
        }
        setError(errorMsg);
      }
    } catch (err: any) {
      console.error('Session lookup error:', err);
      setError('Unable to connect to server. Please check your internet connection.');
    } finally {
      setLoading(false);
    }
  };

  // Handle QR code scan - extract registration code and lookup
  const handleQRCodeScan = async (decodedText: string) => {
    setShowQRScanner(false);

    // Extract registration code from QR data
    // QR code format: https://churchflow.ailabsafrica.com/self-checkin?code=REG-XXXXXXXX
    let code = decodedText.trim();

    // Try to extract code from URL query parameter first
    if (code.includes('?code=') || code.includes('&code=')) {
      const match = code.match(/[?&]code=([^&\s]+)/i);
      if (match) {
        code = match[1].toUpperCase();
      }
    } else if (code.includes('/')) {
      // Fallback: If it's a URL path, try to extract the last segment
      const parts = code.split('/');
      code = parts[parts.length - 1].toUpperCase();
    } else {
      // Just the code itself
      code = code.toUpperCase();
    }

    // Clean up the code - remove any non-alphanumeric except dashes
    code = code.replace(/[^A-Z0-9-]/g, '');

    if (!code || code.length < 5) {
      setError('Invalid QR code. Please try again.');
      return;
    }

    // Set the code and trigger lookup
    setSessionCode(code);

    try {
      setLoading(true);
      setError(null);
      setSessionLookupData(null);
      setTodaysSessions([]);
      setSelectedSession(null);
      setShowRegistrationPrompt(false);

      const response = await fetch(
        getApiUrl(`member/sessions/today/${code}`)
      );

      const data = await response.json();

      if (response.ok) {
        setSessionLookupData(data);
        setTodaysSessions(data.todays_sessions || []);
        setSessionVenue({
          latitude: data.venue_latitude,
          longitude: data.venue_longitude,
          radius: data.venue_checkin_radius || 1000,
          locationRequired: data.location_checkin_required !== false,
        });
        // Auto-get location only if required
        if (data.location_checkin_required !== false) {
          getUserLocation();
        }
      } else {
        // Check if this is a "not found" error
        const errorMsg = data.detail || 'Registration not found for this QR code';
        if (response.status === 404 || errorMsg.toLowerCase().includes('not found') || errorMsg.toLowerCase().includes('no registration')) {
          setShowRegistrationPrompt(true);
        }
        setError(errorMsg);
      }
    } catch (err: any) {
      console.error('QR lookup error:', err);
      setError('Unable to connect to server. Please check your internet connection.');
    } finally {
      setLoading(false);
    }
  };

  // Session check-in: lookup by phone
  const handleSessionLookupByPhone = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!sessionPhone.trim()) {
      setError('Please enter your phone number');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setPhoneRegistrations([]);
      setSelectedPhoneReg(null);
      setTodaysSessions([]);
      setShowRegistrationPrompt(false);

      const response = await fetch(
        getApiUrl(`member/registrations/by-phone/${encodeURIComponent(sessionPhone.trim())}`)
      );

      const data = await response.json();

      if (response.ok) {
        if (data.length === 0) {
          // No registrations found
          setShowRegistrationPrompt(true);
          setError('No registrations found for this phone number');
        } else {
          setPhoneRegistrations(data);
          // If only one registration, auto-select it
          if (data.length === 1) {
            handleSelectPhoneRegistration(data[0]);
          }
        }
      } else {
        // Check if this is a "not found" error
        const errorMsg = data.detail || 'No registrations found for this phone number';
        if (response.status === 404 || errorMsg.toLowerCase().includes('not found') || errorMsg.toLowerCase().includes('no registration')) {
          setShowRegistrationPrompt(true);
        }
        setError(errorMsg);
      }
    } catch (err: any) {
      console.error('Phone lookup error:', err);
      setError('Unable to connect to server. Please check your internet connection.');
    } finally {
      setLoading(false);
    }
  };

  // Select a registration from phone lookup results
  const handleSelectPhoneRegistration = async (reg: PhoneRegistration) => {
    setSelectedPhoneReg(reg);

    // Now fetch today's sessions for this registration
    try {
      setLoading(true);
      const response = await fetch(
        getApiUrl(`member/sessions/today/${reg.registration_code}`)
      );

      const data = await response.json();

      if (response.ok) {
        setSessionLookupData(data);
        setTodaysSessions(data.todays_sessions || []);
        setSessionVenue({
          latitude: data.venue_latitude,
          longitude: data.venue_longitude,
          radius: data.venue_checkin_radius || 1000,
          locationRequired: data.location_checkin_required !== false,
        });
        // Auto-get location only if required
        if (data.location_checkin_required !== false) {
          getUserLocation();
        }
      } else {
        setError(data.detail || 'Failed to fetch sessions');
      }
    } catch (err: any) {
      console.error('Sessions fetch error:', err);
      setError('Failed to fetch sessions');
    } finally {
      setLoading(false);
    }
  };

  // Handle session check-in
  const handleSessionCheckIn = async () => {
    if (!selectedSession) return;
    // Only require location if locationRequired is true
    const locationRequired = sessionVenue?.locationRequired !== false;
    if (locationRequired && !userLocation) return;

    const regCode = sessionLookupData?.registration_id
      ? (sessionCode || selectedPhoneReg?.registration_code)
      : selectedPhoneReg?.registration_code;

    if (!regCode && !sessionPhone) {
      setError('Registration information not found');
      return;
    }

    // Use actual location if available, otherwise use 0,0 (backend skips validation when not required)
    const lat = userLocation?.latitude ?? 0;
    const lon = userLocation?.longitude ?? 0;

    try {
      setCheckingIn(true);
      setError(null);

      let response;
      if (sessionLookupMethod === 'code' || (sessionLookupData && sessionCode)) {
        response = await fetch(
          getApiUrl(`member/sessions/${selectedSession.id}/check-in`),
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              registration_code: sessionCode || selectedPhoneReg?.registration_code,
              latitude: lat,
              longitude: lon,
            }),
          }
        );
      } else {
        response = await fetch(
          getApiUrl(`member/sessions/${selectedSession.id}/check-in/phone`),
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              phone: sessionPhone,
              latitude: lat,
              longitude: lon,
            }),
          }
        );
      }

      const data = await response.json();

      if (response.ok) {
        setSessionCheckInSuccess(true);
        setSessionCheckInData(data);
        // Update the session's checked_in status
        setTodaysSessions((prev) =>
          prev.map((s) =>
            s.id === selectedSession.id ? { ...s, already_checked_in: true } : s
          )
        );
        setSelectedSession(null);
      } else {
        if (response.status === 403) {
          setError(data.detail || 'You are too far from the venue to check in.');
        } else if (response.status === 400) {
          setError(data.detail || 'Already checked in to this session.');
        } else {
          setError(data.detail || 'Check-in failed. Please try again.');
        }
      }
    } catch (err: any) {
      console.error('Session check-in error:', err);
      setError('Unable to connect to server. Please check your internet connection.');
    } finally {
      setCheckingIn(false);
    }
  };

  // Reset session check-in form
  const handleSessionReset = () => {
    setSessionCode('');
    setSessionPhone('');
    setSessionLookupData(null);
    setPhoneRegistrations([]);
    setSelectedPhoneReg(null);
    setTodaysSessions([]);
    setSelectedSession(null);
    setSessionCheckInSuccess(false);
    setSessionCheckInData(null);
    setSessionVenue(null);
    setUserLocation(null);
    setDistance(null);
    setError(null);
    setShowRegistrationPrompt(false);
  };

  // Check if session check-in is enabled
  const isSessionCheckInEnabled = (): boolean => {
    if (!selectedSession || selectedSession.already_checked_in) return false;
    // If location is not required, allow check-in without location verification
    if (sessionVenue?.locationRequired === false) return true;
    // Otherwise, require location verification
    if (!userLocation || distance === null) return false;
    const radius = sessionVenue?.radius || 1000;
    if (distance > radius) return false;
    return true;
  };

  // Update distance when venue changes
  useEffect(() => {
    if (
      userLocation &&
      sessionVenue?.latitude !== undefined &&
      sessionVenue?.longitude !== undefined
    ) {
      const dist = calculateDistance(
        userLocation.latitude,
        userLocation.longitude,
        sessionVenue.latitude,
        sessionVenue.longitude
      );
      setDistance(dist);
    }
  }, [userLocation, sessionVenue]);

  return (
    <div className="min-h-screen bg-gray-50 py-6 sm:py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header with Back Button */}
        <div className="mb-8">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-gray-500 hover:text-purple-600 transition-colors text-sm mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Home</span>
          </Link>
          <div className="text-center">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">Session Check-In</h1>
            <p className="text-gray-500">
              Check in to your conference sessions using QR code, phone number, or registration code
            </p>
          </div>
        </div>

        {/* Tab Navigation - Conference tab hidden */}
        {/* To show conference tab, uncomment the div below */}
        {/*
        <div className="flex border-b border-gray-200 mb-6">
          <button
            onClick={() => {
              setActiveTab('conference');
              handleSessionReset();
            }}
            className={`flex-1 py-3 px-4 text-center font-medium transition-colors ${
              activeTab === 'conference'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Calendar className="w-5 h-5 inline-block mr-2" />
            Conference Check-In
          </button>
          <button
            onClick={() => {
              setActiveTab('session');
              handleReset();
            }}
            className={`flex-1 py-3 px-4 text-center font-medium transition-colors ${
              activeTab === 'session'
                ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <List className="w-5 h-5 inline-block mr-2" />
            Session Check-In
          </button>
        </div>
        */}

        {/* ============ CONFERENCE CHECK-IN TAB ============ */}
        {activeTab === 'conference' && (
          <>
            {/* Conference Check-in Success Screen */}
            {checkInSuccess && checkInData && (
              <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
                <div className="text-center">
                  <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-12 h-12 text-green-600" />
                  </div>

                  <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
                    Welcome, {checkInData.user_name}!
                  </h2>

                  {checkInData.is_repeat_checkin && (
                    <div className="inline-flex items-center bg-blue-100 text-blue-800 px-4 py-2 rounded-full mb-4">
                      <AlertCircle className="w-5 h-5 mr-2" />
                      You were already checked in
                    </div>
                  )}

                  <p className="text-xl text-gray-700 mb-2">{checkInData.conference_name}</p>
                  <p className="text-gray-500 mb-6">
                    Checked in at {formatDate(checkInData.checked_in_at)}
                  </p>

                  {/* Voice Greeting */}
                  {checkInData.greeting_audio && (
                    <div className="mb-6">
                      <GreetingAudioPlayer
                        greetingAudio={checkInData.greeting_audio}
                        userName={checkInData.user_name}
                      />
                    </div>
                  )}

                  <button
                    onClick={handleReset}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                  >
                    Check In Another Registration
                  </button>
                </div>
              </div>
            )}

        {/* Registration Lookup Form */}
        {!checkInSuccess && !registration && (
          <div className="card-elevated p-6">
            <form onSubmit={handleLookup} className="space-y-5">
              <div>
                <label className="label">Registration Code</label>
                <input
                  type="text"
                  value={registrationCode}
                  onChange={(e) => setRegistrationCode(e.target.value.toUpperCase())}
                  placeholder="REG-XXXXXXXX"
                  className="input uppercase"
                  disabled={loading}
                />
                <p className="helper-text">
                  Enter the registration code from your confirmation email or QR code
                </p>
              </div>

              {error && (
                <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 text-red-800 rounded-lg">
                  <XCircle className="w-5 h-5 flex-shrink-0" />
                  <p>{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !registrationCode.trim()}
                className="btn-primary w-full py-2.5"
              >
                {loading ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    Looking up registration...
                  </>
                ) : (
                  'View My Registration'
                )}
              </button>
            </form>
          </div>
        )}

        {/* Registration Details & Check-In */}
        {!checkInSuccess && registration && (
          <div className="space-y-6">
            {/* Conference Info Card */}
            <div className="card-elevated p-6">
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-1">
                  {registration.conference_name}
                </h2>
                <div className="flex items-center gap-2 text-sm">
                  <span
                    className={`px-3 py-1 rounded-full ${
                      registration.checked_in
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {registration.checked_in ? 'Checked In' : 'Not Checked In'}
                  </span>
                </div>
              </div>

              {/* Registration Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="flex items-start gap-3">
                  <User className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-500">Name</p>
                    <p className="font-medium">{registration.user_name}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Phone className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-500">Phone</p>
                    <p className="font-medium">{registration.user_phone}</p>
                  </div>
                </div>

                {registration.user_email && (
                  <div className="flex items-start gap-3">
                    <Mail className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Email</p>
                      <p className="font-medium">{registration.user_email}</p>
                    </div>
                  </div>
                )}

                <div className="flex items-start gap-3">
                  <Church className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm text-gray-500">Branch/Church</p>
                    <p className="font-medium">
                      {registration.branch_name || registration.church_name || 'N/A'}
                    </p>
                  </div>
                </div>

                {registration.conference_start_date && (
                  <div className="flex items-start gap-3">
                    <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Start Date</p>
                      <p className="font-medium">{formatDate(registration.conference_start_date)}</p>
                    </div>
                  </div>
                )}

                {registration.venue && (
                  <div className="flex items-start gap-3">
                    <MapPin className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Venue</p>
                      <p className="font-medium">{registration.venue}</p>
                    </div>
                  </div>
                )}

                {registration.requires_bus && (
                  <div className="flex items-start gap-3">
                    <Bus className="w-5 h-5 text-gray-400 mt-0.5" />
                    <div>
                      <p className="text-sm text-gray-500">Bus Transport</p>
                      <p className="font-medium">
                        {registration.bus_route_name || 'Yes'}
                        {registration.pickup_location && ` (${registration.pickup_location})`}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {registration.checked_in && registration.checked_in_at && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <p className="text-green-800">
                      You checked in on {formatDate(registration.checked_in_at)}
                    </p>
                  </div>
                </div>
              )}

              {/* Location-Based Check-In Section */}
              {!registration.checked_in && registration.self_checkin_enabled && (
                <div className="border-t pt-6">
                  <h3 className="text-lg font-semibold mb-4">Location-Based Check-In</h3>

                  {/* Location Status */}
                  {!userLocation && !locationError && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                      <div className="flex items-start gap-3">
                        <Navigation className="w-5 h-5 text-blue-600 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-blue-900 font-medium mb-2">
                            Enable location to check in
                          </p>
                          <p className="text-blue-700 text-sm mb-3">
                            You must be within {registration.venue_checkin_radius || 1000}m of the
                            venue to check in
                          </p>
                          <button
                            onClick={getUserLocation}
                            disabled={checkingLocation}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition flex items-center gap-2"
                          >
                            {checkingLocation ? (
                              <>
                                <Loader className="w-4 h-4 animate-spin" />
                                Getting location...
                              </>
                            ) : (
                              <>
                                <Navigation className="w-4 h-4" />
                                Get My Location
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {locationError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                      <div className="flex items-start gap-3">
                        <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-red-900 font-medium mb-1">Location Error</p>
                          <p className="text-red-700 text-sm mb-3">{locationError}</p>
                          <button
                            onClick={getUserLocation}
                            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm"
                          >
                            Try Again
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {userLocation && distance !== null && (
                    <div
                      className={`border rounded-lg p-4 mb-4 ${
                        distance <= (registration.venue_checkin_radius || 1000)
                          ? 'bg-green-50 border-green-200'
                          : 'bg-yellow-50 border-yellow-200'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <MapPin
                          className={`w-5 h-5 mt-0.5 ${
                            distance <= (registration.venue_checkin_radius || 1000)
                              ? 'text-green-600'
                              : 'text-yellow-600'
                          }`}
                        />
                        <div className="flex-1">
                          <p
                            className={`font-medium mb-1 ${
                              distance <= (registration.venue_checkin_radius || 1000)
                                ? 'text-green-900'
                                : 'text-yellow-900'
                            }`}
                          >
                            {distance <= (registration.venue_checkin_radius || 1000)
                              ? 'You are within check-in range! ✓'
                              : 'You are too far from the venue'}
                          </p>
                          <p
                            className={`text-sm ${
                              distance <= (registration.venue_checkin_radius || 1000)
                                ? 'text-green-700'
                                : 'text-yellow-700'
                            }`}
                          >
                            Distance: {distance.toFixed(0)}m (Maximum:{' '}
                            {registration.venue_checkin_radius || 1000}m)
                          </p>
                          {distance > (registration.venue_checkin_radius || 1000) && (
                            <p className="text-sm text-yellow-700 mt-2">
                              Please move closer to the venue to enable check-in
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {error && (
                    <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 text-red-800 rounded-lg mb-4">
                      <XCircle className="w-5 h-5 flex-shrink-0" />
                      <p>{error}</p>
                    </div>
                  )}

                  {/* Check-In Button */}
                  <button
                    onClick={handleCheckIn}
                    disabled={!isCheckInEnabled() || checkingIn}
                    className={`w-full py-4 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
                      isCheckInEnabled() && !checkingIn
                        ? 'bg-green-600 text-white hover:bg-green-700'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    {checkingIn ? (
                      <>
                        <Loader className="w-5 h-5 animate-spin" />
                        Checking in...
                      </>
                    ) : isCheckInEnabled() ? (
                      <>
                        <CheckCircle className="w-5 h-5" />
                        Check In Now
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-5 h-5" />
                        Check-In Unavailable
                      </>
                    )}
                  </button>

                  {!isCheckInEnabled() && !checkingIn && (
                    <p className="text-sm text-gray-500 text-center mt-2">
                      {!userLocation
                        ? 'Enable location to check in'
                        : distance !== null &&
                          distance > (registration.venue_checkin_radius || 1000)
                        ? 'Move closer to the venue'
                        : 'Check-in requirements not met'}
                    </p>
                  )}
                </div>
              )}

              {!registration.checked_in && !registration.self_checkin_enabled && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-gray-600 mt-0.5" />
                    <div>
                      <p className="text-gray-900 font-medium mb-1">
                        Self check-in is not enabled
                      </p>
                      <p className="text-gray-600 text-sm">
                        Please check in with event staff at the registration desk
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <button
                onClick={handleReset}
                className="flex-1 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
              >
                Look Up Different Registration
              </button>
            </div>
          </div>
        )}
          </>
        )}

        {/* ============ SESSION CHECK-IN TAB ============ */}
        {activeTab === 'session' && (
          <>
            {/* Session Check-in Success Screen */}
            {sessionCheckInSuccess && sessionCheckInData && (
              <div className="card p-8 mb-6 animate-fade-in">
                <div className="text-center">
                  <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-8 h-8 text-purple-600" />
                  </div>

                  <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
                    Session Check-In Successful!
                  </h2>

                  <p className="text-lg text-gray-700 mb-1">{sessionCheckInData.session_name}</p>
                  <p className="text-gray-500 mb-1">{sessionCheckInData.user_name}</p>
                  <p className="text-sm text-gray-400 mb-4">
                    Checked in at {formatDate(sessionCheckInData.checked_in_at)}
                  </p>

                  {/* Voice Greeting */}
                  {sessionCheckInData.greeting_audio && (
                    <div className="mb-6">
                      <GreetingAudioPlayer
                        greetingAudio={sessionCheckInData.greeting_audio}
                        userName={sessionCheckInData.user_name}
                        autoPlay={true}
                      />
                    </div>
                  )}

                  <div className="flex gap-3 justify-center">
                    <button
                      onClick={() => {
                        setSessionCheckInSuccess(false);
                        setSessionCheckInData(null);
                      }}
                      className="btn-primary"
                    >
                      Check In to Another Session
                    </button>
                    <button
                      onClick={handleSessionReset}
                      className="btn-secondary"
                    >
                      Start Over
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Session Lookup Form */}
            {!sessionCheckInSuccess && !sessionLookupData && phoneRegistrations.length === 0 && (
              <div className="card">
                {/* Lookup Method Tabs */}
                <div className="flex gap-1 p-1 bg-gray-100 rounded-lg mb-6">
                  <button
                    onClick={() => {
                      setSessionLookupMethod('qr');
                      setError(null);
                    }}
                    className={`flex-1 py-2.5 text-center font-medium transition-all rounded-md text-sm ${
                      sessionLookupMethod === 'qr'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <QrCode className="w-4 h-4 inline-block mr-1.5" />
                    QR Code
                  </button>
                  <button
                    onClick={() => {
                      setSessionLookupMethod('phone');
                      setError(null);
                    }}
                    className={`flex-1 py-2.5 text-center font-medium transition-all rounded-md text-sm ${
                      sessionLookupMethod === 'phone'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <Phone className="w-4 h-4 inline-block mr-1.5" />
                    Phone
                  </button>
                  <button
                    onClick={() => {
                      setSessionLookupMethod('code');
                      setError(null);
                    }}
                    className={`flex-1 py-2.5 text-center font-medium transition-all rounded-md text-sm ${
                      sessionLookupMethod === 'code'
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    Code
                  </button>
                </div>

                {/* QR Scan Option */}
                {sessionLookupMethod === 'qr' && (
                  <div className="space-y-6">
                    <div className="text-center py-6">
                      <div className="w-16 h-16 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                        <Camera className="w-8 h-8 text-purple-600" />
                      </div>
                      <h3 className="font-semibold text-gray-900 mb-2">
                        Scan Your Registration QR Code
                      </h3>
                      <p className="text-sm text-gray-500 mb-6">
                        Use your camera to scan the QR code from your registration email or badge
                      </p>
                      <button
                        onClick={() => setShowQRScanner(true)}
                        className="btn-primary inline-flex items-center gap-2"
                      >
                        <Camera className="w-4 h-4" />
                        Open Camera Scanner
                      </button>
                    </div>

                    {error && (
                      <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
                        <XCircle className="w-4 h-4 flex-shrink-0" />
                        <p>{error}</p>
                      </div>
                    )}

                    {/* Registration Prompt */}
                    {showRegistrationPrompt && (
                      <div className="bg-purple-50 border border-purple-200 rounded-lg p-5 text-center">
                        <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                          <User className="w-6 h-6 text-purple-600" />
                        </div>
                        <h4 className="font-semibold text-gray-900 mb-2">Not Registered Yet?</h4>
                        <p className="text-sm text-gray-600 mb-4">
                          Please register for the conference first before checking in.
                        </p>
                        <Link
                          to="/register"
                          className="btn-primary inline-flex items-center gap-2"
                        >
                          <Calendar className="w-4 h-4" />
                          Register Now
                        </Link>
                      </div>
                    )}
                  </div>
                )}

                {/* Code Lookup Form */}
                {sessionLookupMethod === 'code' && (
                  <form onSubmit={handleSessionLookupByCode} className="space-y-4">
                    <div>
                      <label className="label">Registration Code</label>
                      <input
                        type="text"
                        value={sessionCode}
                        onChange={(e) => setSessionCode(e.target.value.toUpperCase())}
                        placeholder="REG-XXXXXXXX"
                        className="input uppercase"
                        disabled={loading}
                      />
                    </div>

                    {error && (
                      <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
                        <XCircle className="w-4 h-4 flex-shrink-0" />
                        <p>{error}</p>
                      </div>
                    )}

                    {/* Registration Prompt */}
                    {showRegistrationPrompt && (
                      <div className="bg-purple-50 border border-purple-200 rounded-lg p-5 text-center">
                        <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                          <User className="w-6 h-6 text-purple-600" />
                        </div>
                        <h4 className="font-semibold text-gray-900 mb-2">Not Registered Yet?</h4>
                        <p className="text-sm text-gray-600 mb-4">
                          Please register for the conference first before checking in.
                        </p>
                        <Link
                          to="/register"
                          className="btn-primary inline-flex items-center gap-2"
                        >
                          <Calendar className="w-4 h-4" />
                          Register Now
                        </Link>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={loading || !sessionCode.trim()}
                      className="btn-primary w-full flex items-center justify-center gap-2"
                    >
                      {loading ? (
                        <>
                          <Loader className="w-4 h-4 animate-spin" />
                          Looking up sessions...
                        </>
                      ) : (
                        "View Today's Sessions"
                      )}
                    </button>
                  </form>
                )}

                {/* Phone Lookup Form */}
                {sessionLookupMethod === 'phone' && (
                  <form onSubmit={handleSessionLookupByPhone} className="space-y-4">
                    <div>
                      <label className="label">Phone Number</label>
                      <input
                        type="tel"
                        value={sessionPhone}
                        onChange={(e) => setSessionPhone(e.target.value)}
                        placeholder="+233XXXXXXXXX"
                        className="input"
                        disabled={loading}
                      />
                      <p className="text-xs text-gray-400 mt-1.5">
                        Enter the phone number you used to register
                      </p>
                    </div>

                    {error && (
                      <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
                        <XCircle className="w-4 h-4 flex-shrink-0" />
                        <p>{error}</p>
                      </div>
                    )}

                    {/* Registration Prompt */}
                    {showRegistrationPrompt && (
                      <div className="bg-purple-50 border border-purple-200 rounded-lg p-5 text-center">
                        <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                          <User className="w-6 h-6 text-purple-600" />
                        </div>
                        <h4 className="font-semibold text-gray-900 mb-2">Not Registered Yet?</h4>
                        <p className="text-sm text-gray-600 mb-4">
                          Please register for the conference first before checking in.
                        </p>
                        <Link
                          to="/register"
                          className="btn-primary inline-flex items-center gap-2"
                        >
                          <Calendar className="w-4 h-4" />
                          Register Now
                        </Link>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={loading || !sessionPhone.trim()}
                      className="btn-primary w-full flex items-center justify-center gap-2"
                    >
                      {loading ? (
                        <>
                          <Loader className="w-4 h-4 animate-spin" />
                          Finding registrations...
                        </>
                      ) : (
                        'Find My Registrations'
                      )}
                    </button>
                  </form>
                )}
              </div>
            )}

            {/* Phone Registrations Selection */}
            {!sessionCheckInSuccess && phoneRegistrations.length > 1 && !selectedPhoneReg && (
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <h3 className="text-lg font-semibold mb-4">Select Your Conference</h3>
                <p className="text-gray-600 mb-4">
                  Multiple registrations found. Please select the conference you want to check into:
                </p>
                <div className="space-y-3">
                  {phoneRegistrations.map((reg) => (
                    <button
                      key={reg.id}
                      onClick={() => handleSelectPhoneRegistration(reg)}
                      className="w-full p-4 border border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition text-left"
                    >
                      <p className="font-medium">{reg.conference_name}</p>
                      <p className="text-sm text-gray-500">{reg.venue}</p>
                    </button>
                  ))}
                </div>
                <button
                  onClick={handleSessionReset}
                  className="mt-4 w-full py-2 text-gray-600 hover:text-gray-800 transition"
                >
                  Start Over
                </button>
              </div>
            )}

            {/* Today's Sessions Display */}
            {!sessionCheckInSuccess && sessionLookupData && (
              <div className="space-y-6">
                {/* User Info */}
                <div className="bg-white rounded-2xl shadow-xl p-6">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                      <User className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg">{sessionLookupData.user_name}</h3>
                      <p className="text-gray-500">{sessionLookupData.conference_name}</p>
                    </div>
                  </div>

                  {/* Location Status - only show if location is required */}
                  {sessionVenue?.locationRequired !== false && !userLocation && !locationError && (
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <Navigation className="w-5 h-5 text-purple-600 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-purple-900 font-medium mb-2">
                            Enable location to check in
                          </p>
                          <p className="text-purple-700 text-sm mb-3">
                            You must be within {sessionVenue?.radius || 1000}m of the venue
                          </p>
                          <button
                            onClick={getUserLocation}
                            disabled={checkingLocation}
                            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 transition flex items-center gap-2"
                          >
                            {checkingLocation ? (
                              <>
                                <Loader className="w-4 h-4 animate-spin" />
                                Getting location...
                              </>
                            ) : (
                              <>
                                <Navigation className="w-4 h-4" />
                                Get My Location
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {sessionVenue?.locationRequired !== false && locationError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
                        <div className="flex-1">
                          <p className="text-red-900 font-medium mb-1">Location Error</p>
                          <p className="text-red-700 text-sm mb-3">{locationError}</p>
                          <button
                            onClick={getUserLocation}
                            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm"
                          >
                            Try Again
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {sessionVenue?.locationRequired !== false && userLocation && distance !== null && (
                    <div
                      className={`border rounded-lg p-4 ${
                        distance <= (sessionVenue?.radius || 1000)
                          ? 'bg-green-50 border-green-200'
                          : 'bg-yellow-50 border-yellow-200'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <MapPin
                          className={`w-5 h-5 mt-0.5 ${
                            distance <= (sessionVenue?.radius || 1000)
                              ? 'text-green-600'
                              : 'text-yellow-600'
                          }`}
                        />
                        <div className="flex-1">
                          <p
                            className={`font-medium mb-1 ${
                              distance <= (sessionVenue?.radius || 1000)
                                ? 'text-green-900'
                                : 'text-yellow-900'
                            }`}
                          >
                            {distance <= (sessionVenue?.radius || 1000)
                              ? 'You are within check-in range!'
                              : 'You are too far from the venue'}
                          </p>
                          <p
                            className={`text-sm ${
                              distance <= (sessionVenue?.radius || 1000)
                                ? 'text-green-700'
                                : 'text-yellow-700'
                            }`}
                          >
                            Distance: {distance.toFixed(0)}m (Maximum: {sessionVenue?.radius || 1000}m)
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Sessions List */}
                <div className="bg-white rounded-2xl shadow-xl p-6">
                  <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <Clock className="w-5 h-5 text-purple-600" />
                    Today's Sessions
                  </h3>

                  {todaysSessions.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p>No sessions scheduled for today</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {todaysSessions.map((session) => (
                        <div
                          key={session.id}
                          className={`p-4 border rounded-lg transition ${
                            session.already_checked_in
                              ? 'bg-green-50 border-green-200'
                              : selectedSession?.id === session.id
                              ? 'border-purple-500 bg-purple-50'
                              : 'border-gray-200 hover:border-purple-300'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <h4 className="font-medium">{session.name}</h4>
                                {session.already_checked_in && (
                                  <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full flex items-center gap-1">
                                    <CheckCircle className="w-3 h-3" />
                                    Checked In
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-gray-500">{session.day_label}</p>
                              {session.location && (
                                <p className="text-sm text-gray-400 flex items-center gap-1 mt-1">
                                  <MapPin className="w-3 h-3" />
                                  {session.location}
                                </p>
                              )}
                            </div>
                            {!session.already_checked_in && (
                              <button
                                onClick={() => setSelectedSession(session)}
                                disabled={sessionVenue?.locationRequired !== false && (!userLocation || distance === null || distance > (sessionVenue?.radius || 1000))}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                                  selectedSession?.id === session.id
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-purple-100 hover:text-purple-700 disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed'
                                }`}
                              >
                                {selectedSession?.id === session.id ? 'Selected' : 'Select'}
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Error Display */}
                  {error && (
                    <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 text-red-800 rounded-lg mt-4">
                      <XCircle className="w-5 h-5 flex-shrink-0" />
                      <p>{error}</p>
                    </div>
                  )}

                  {/* Check-in Button */}
                  {selectedSession && (
                    <button
                      onClick={handleSessionCheckIn}
                      disabled={!isSessionCheckInEnabled() || checkingIn}
                      className={`w-full mt-4 py-4 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
                        isSessionCheckInEnabled() && !checkingIn
                          ? 'bg-purple-600 text-white hover:bg-purple-700'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      {checkingIn ? (
                        <>
                          <Loader className="w-5 h-5 animate-spin" />
                          Checking in...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-5 h-5" />
                          Check In to {selectedSession.name}
                        </>
                      )}
                    </button>
                  )}
                </div>

                {/* Reset Button */}
                <button
                  onClick={handleSessionReset}
                  className="w-full py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
                >
                  Look Up Different Registration
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* QR Scanner Modal */}
      {showQRScanner && (
        <CameraQRScanner
          onScan={handleQRCodeScan}
          onClose={() => setShowQRScanner(false)}
        />
      )}
    </div>
  );
}
