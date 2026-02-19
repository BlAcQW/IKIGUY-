import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import axios from 'axios';
import PhoneInput, { isValidPhoneNumber } from 'react-phone-number-input';
import 'react-phone-number-input/style.css';
import SearchableBranchSelect from '../components/SearchableBranchSelect';
import SearchableBusRouteSelect from '../components/SearchableBusRouteSelect';

const API_BASE = '/api/v1';

interface Branch {
  id: string;
  name: string;
  location: string;
  capacity: number;
}

interface BusRoute {
  id: string;
  name?: string;
  route_name?: string;
  departure_location: string;
  departure_time: string;
}

interface Conference {
  id: string;
  name: string;
  description: string;
  start_date: string;
  end_date: string;
  venue: string;
  venue_latitude?: number;
  venue_longitude?: number;
  venue_checkin_radius?: number;
  expected_attendance: number;
  registration_open: boolean;
}

interface Session {
  id: string;
  name: string;
  description?: string;
  location?: string;
  session_date: string;
  day_number: number;
  day_label: string;
}

interface Registration {
  id: string;
  registration_code: string;
  qr_code: string;
  conference_name: string;
  user_name: string;
  branch_name?: string;
  church_name?: string;
  bus_route_name?: string;
  pickup_location?: string;
  session_checked_in?: boolean;
  session_name?: string;
  session_check_in_warning?: string;
}

export default function ConferenceRegistration() {
  const { conferenceId } = useParams<{ conferenceId?: string }>();
  const navigate = useNavigate();

  const [conference, setConference] = useState<Conference | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [busRoutes, setBusRoutes] = useState<BusRoute[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [registration, setRegistration] = useState<Registration | null>(null);

  // Ref to track greeting audio for proper cleanup
  const greetingAudioRef = useRef<HTMLAudioElement | null>(null);

  // Session selection state (for on-site registration)
  const [isConferenceOngoing, setIsConferenceOngoing] = useState(false);
  const [userLocation, setUserLocation] = useState<{lat: number, lon: number} | null>(null);
  const [isWithinVenue, setIsWithinVenue] = useState(false);
  const [todaysSessions, setTodaysSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  const [locationStatus, setLocationStatus] = useState<'checking' | 'granted' | 'denied' | null>(null);

  // Church type selection state
  const [churchType, setChurchType] = useState<'aci' | 'other' | ''>('');

  // Form state
  const [formData, setFormData] = useState({
    user_name: '',
    user_phone: '',
    user_email: '',
    branch_id: '',
    church_name: '',
    requires_bus: false,
    bus_route_id: '',
    special_needs: '',
    emergency_contact: ''
  });

  useEffect(() => {
    loadData();
  }, [conferenceId]);

  // Cleanup greeting audio on unmount or when registration changes
  useEffect(() => {
    return () => {
      if (greetingAudioRef.current) {
        greetingAudioRef.current.pause();
        greetingAudioRef.current.src = '';
        greetingAudioRef.current = null;
      }
    };
  }, [registration]);

  // Haversine distance calculation (returns distance in meters)
  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
    const R = 6371000; // Earth's radius in meters
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c; // Distance in meters
  };

  const loadData = async () => {
    try {
      setLoading(true);

      // Load conference
      let conferenceData: Conference | null = null;
      if (conferenceId) {
        const confResponse = await axios.get(`${API_BASE}/conferences/${conferenceId}`);
        conferenceData = confResponse.data;
        setConference(conferenceData);
      } else {
        // Load latest conference
        const confsResponse = await axios.get(`${API_BASE}/conferences`);
        if (confsResponse.data.length > 0) {
          conferenceData = confsResponse.data[0];
          setConference(conferenceData);
        }
      }

      // Load branches
      const branchesResponse = await axios.get(`${API_BASE}/branches`);
      setBranches(branchesResponse.data);

      // Load bus routes
      const busResponse = await axios.get(`${API_BASE}/buses/routes`);
      setBusRoutes(busResponse.data);

      // Check if conference is ongoing and handle location-based session selection
      if (conferenceData) {
        const now = new Date();
        const startDate = new Date(conferenceData.start_date);
        const endDate = new Date(conferenceData.end_date);
        const ongoing = now >= startDate && now <= endDate;
        setIsConferenceOngoing(ongoing);

        if (ongoing && conferenceData.venue_latitude && conferenceData.venue_longitude) {
          // Request location permission
          console.log('🔵 Conference is ongoing, requesting location...');
          setLocationStatus('checking');
          if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
              async (position) => {
                const { latitude, longitude } = position.coords;
                console.log('🔵 User location:', { latitude, longitude });
                setUserLocation({ lat: latitude, lon: longitude });
                setLocationStatus('granted');

                // Check if within venue radius
                const distance = calculateDistance(
                  latitude,
                  longitude,
                  conferenceData!.venue_latitude!,
                  conferenceData!.venue_longitude!
                );

                const venueRadius = conferenceData!.venue_checkin_radius || 1000;
                const withinVenue = distance <= venueRadius;
                console.log('🔵 Distance check:', {
                  distance: distance.toFixed(2) + 'm',
                  venueRadius: venueRadius + 'm',
                  withinVenue,
                  venueCoords: { lat: conferenceData!.venue_latitude, lon: conferenceData!.venue_longitude }
                });
                setIsWithinVenue(withinVenue);

                if (withinVenue) {
                  // Fetch today's sessions
                  console.log('🔵 Within venue! Fetching today\'s sessions...');
                  try {
                    const sessionsRes = await axios.get(
                      `${API_BASE}/conferences/${conferenceData!.id}/sessions/today-public`
                    );
                    console.log('🔵 Today\'s sessions:', sessionsRes.data);
                    setTodaysSessions(sessionsRes.data);
                  } catch (err) {
                    console.error('❌ Failed to load today\'s sessions:', err);
                  }
                } else {
                  console.log('❌ Not within venue radius. Distance:', distance.toFixed(2) + 'm');
                }
              },
              (error) => {
                console.error('❌ Location error:', error);
                setLocationStatus('denied');
              },
              { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
            );
          }
        } else {
          console.log('🔵 Conference check:', {
            ongoing,
            hasVenueLat: !!conferenceData.venue_latitude,
            hasVenueLon: !!conferenceData.venue_longitude,
            startDate: conferenceData.start_date,
            endDate: conferenceData.end_date,
            now: new Date()
          });
        }
      }

    } catch (err: any) {
      console.error('Error loading data:', err);
      setError(err.response?.data?.detail || 'Failed to load registration data');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;

    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleChurchTypeChange = (type: 'aci' | 'other') => {
    setChurchType(type);
    // Reset church selection when switching types
    setFormData(prev => ({ ...prev, branch_id: '', church_name: '' }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!conference) {
      setError('No conference selected');
      return;
    }

    if (!formData.user_name || !formData.user_phone) {
      setError('Please fill in all required fields');
      return;
    }

    // Validate phone number format
    if (formData.user_phone && !isValidPhoneNumber(formData.user_phone)) {
      setError('Please enter a valid phone number');
      return;
    }

    // Validate church type is selected
    if (!churchType) {
      setError('Please select your church type');
      return;
    }

    // Validate branch is selected for ACI
    if (churchType === 'aci' && !formData.branch_id) {
      setError('Please select your Action Chapel International branch');
      return;
    }

    // Validate church name is entered for Other
    if (churchType === 'other' && !formData.church_name) {
      setError('Please enter your church name');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const payload: any = {
        conference_id: conference.id,
        user_name: formData.user_name,
        user_phone: formData.user_phone,
        user_email: formData.user_email || null,
        branch_id: churchType === 'aci' ? formData.branch_id : null,
        church_name: churchType === 'other' ? formData.church_name : null,
        requires_bus: formData.requires_bus,
        bus_route_id: (formData.requires_bus && formData.bus_route_id) ? formData.bus_route_id : null,
        special_needs: formData.special_needs || null,
        emergency_contact: formData.emergency_contact || null
      };

      // Add session check-in fields if applicable
      if (selectedSessionId && userLocation) {
        payload.session_id = selectedSessionId;
        payload.latitude = userLocation.lat;
        payload.longitude = userLocation.lon;
      }

      const response = await axios.post(`${API_BASE}/registrations/`, payload);

      setRegistration(response.data);

      // Show success with session info if checked in
      if (response.data.session_checked_in && response.data.greeting_audio) {
        // Play greeting audio if available
        try {
          // Clean up any existing audio first
          if (greetingAudioRef.current) {
            greetingAudioRef.current.pause();
            greetingAudioRef.current.src = '';
          }

          // Create and play new audio with proper error handling
          const audio = new Audio(response.data.greeting_audio);
          greetingAudioRef.current = audio;

          // Handle the play promise to prevent unhandled rejection
          audio.play().catch((err) => {
            console.error('Failed to play greeting audio:', err);
            // Clear the ref if play fails
            if (greetingAudioRef.current === audio) {
              greetingAudioRef.current = null;
            }
          });

          // Clean up when audio finishes playing
          audio.addEventListener('ended', () => {
            if (greetingAudioRef.current === audio) {
              greetingAudioRef.current = null;
            }
          }, { once: true });

        } catch (err) {
          console.error('Failed to create greeting audio:', err);
        }
      }
    } catch (err: any) {
      console.error('Registration error:', err);
      console.error('Error response:', err.response?.data);

      // Show detailed validation error if available
      let errorMessage = 'Failed to register for conference';
      if (err.response?.data?.detail) {
        if (Array.isArray(err.response.data.detail)) {
          // Pydantic validation errors
          errorMessage = err.response.data.detail.map((e: any) => e.msg).join(', ');
        } else {
          errorMessage = err.response.data.detail;
        }
      }
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDownloadQR = () => {
    if (!registration || !registration.qr_code) return;

    const link = document.createElement('a');
    link.href = registration.qr_code;
    link.download = `${registration.registration_code}.png`;
    link.click();
  };

  const handleRegisterAnother = () => {
    // Stop any playing greeting audio
    if (greetingAudioRef.current) {
      greetingAudioRef.current.pause();
      greetingAudioRef.current.src = '';
      greetingAudioRef.current = null;
    }

    setRegistration(null);
    setChurchType('');
    setFormData({
      user_name: '',
      user_phone: '',
      user_email: '',
      branch_id: '',
      church_name: '',
      requires_bus: false,
      bus_route_id: '',
      special_needs: '',
      emergency_contact: ''
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!conference) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">No conference available for registration</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (registration) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 py-12 px-4">
        <div className="max-w-2xl mx-auto">
          {/* Back to Home Navigation */}
          <div className="mb-4">
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-gray-500 hover:text-indigo-600 transition-colors text-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Home</span>
            </Link>
          </div>

          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Registration Successful!</h2>
              <p className="text-gray-600 mb-6">You're registered for {registration.conference_name}</p>

              {/* QR Code */}
              <div className="bg-gray-50 rounded-xl p-6 mb-6">
                <p className="text-sm text-gray-600 mb-4">Your Check-in QR Code</p>
                {registration.qr_code && (
                  <img
                    src={registration.qr_code}
                    alt="Registration QR Code"
                    loading="eager"
                    className="mx-auto w-48 h-48 sm:w-64 sm:h-64"
                  />
                )}
                <p className="mt-4 text-2xl font-mono font-bold text-indigo-600">
                  {registration.registration_code}
                </p>
                <p className="text-sm text-gray-500 mt-2">Show this code at check-in</p>
              </div>

              {/* Registration Details */}
              <div className="bg-gray-50 rounded-xl p-6 mb-6 text-left">
                <h3 className="font-semibold text-gray-900 mb-3">Registration Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Name:</span>
                    <span className="font-medium">{registration.user_name}</span>
                  </div>
                  {registration.branch_name && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Branch:</span>
                      <span className="font-medium">{registration.branch_name}</span>
                    </div>
                  )}
                  {registration.church_name && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Church:</span>
                      <span className="font-medium">{registration.church_name}</span>
                    </div>
                  )}
                  {registration.bus_route_name && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Pick Up Point:</span>
                      <span className="font-medium">{registration.bus_route_name}</span>
                    </div>
                  )}
                  {registration.pickup_location && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Bus Route:</span>
                      <span className="font-medium">{registration.pickup_location}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-4 justify-center">
                <button
                  onClick={handleDownloadQR}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Download QR Code
                </button>
                <button
                  onClick={handleRegisterAnother}
                  className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Register Another
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 py-4 sm:py-8 lg:py-12 px-2 sm:px-4">
      <div className="max-w-4xl mx-auto">
        {/* Back to Home Navigation */}
        <div className="mb-4">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-gray-500 hover:text-indigo-600 transition-colors text-sm"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Home</span>
          </Link>
        </div>

        {/* Conference Banner Image */}
        <div className="mb-4 sm:mb-6 lg:mb-8 rounded-lg sm:rounded-xl lg:rounded-2xl overflow-hidden shadow-lg sm:shadow-xl">
          <img
            src="/impact-2025-banner.jpg"
            alt="IMPACT 2025 Conference Banner"
            loading="lazy"
            className="w-full h-auto object-cover max-h-[200px] sm:max-h-[300px] lg:max-h-none"
          />
        </div>

        <div className="bg-white rounded-xl sm:rounded-2xl shadow-xl p-4 sm:p-6 lg:p-8">
          {/* Conference Header */}
          <div className="mb-6 sm:mb-8 text-center">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">{conference.name}</h1>
            <p className="text-sm sm:text-base text-gray-600 mb-4">{conference.description}</p>
            <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-6 text-xs sm:text-sm text-gray-600">
              <div>
                <span className="font-medium">📅 Dates:</span>{' '}
                {new Date(conference.start_date).toLocaleDateString()} -{' '}
                {new Date(conference.end_date).toLocaleDateString()}
              </div>
              <div>
                <span className="font-medium">📍 Venue:</span> {conference.venue}
              </div>
            </div>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Personal Information */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Personal Information</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="user_name"
                    value={formData.user_name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Enter your full name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number <span className="text-red-500">*</span>
                  </label>
                  <PhoneInput
                    international
                    defaultCountry="GH"
                    value={formData.user_phone}
                    onChange={(value) => setFormData(prev => ({ ...prev, user_phone: value || '' }))}
                    className="phone-input-custom w-full"
                    placeholder="Enter phone number"
                    required
                    style={{ fontSize: '16px', minHeight: '44px' }}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address (Optional)
                  </label>
                  <input
                    type="email"
                    name="user_email"
                    value={formData.user_email}
                    onChange={handleInputChange}
                    className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="email@example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Emergency Contact (Optional)
                  </label>
                  <PhoneInput
                    international
                    defaultCountry="GH"
                    value={formData.emergency_contact}
                    onChange={(value) => setFormData(prev => ({ ...prev, emergency_contact: value || '' }))}
                    className="phone-input-custom w-full"
                    placeholder="Enter emergency contact number"
                  />
                </div>
              </div>
            </div>

            {/* Church Selection */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Church Information</h3>

              <div className="space-y-4">
                {/* Church Type Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Select Your Church <span className="text-red-500">*</span>
                  </label>
                  <div className="space-y-3">
                    {/* Action Chapel International Option */}
                    <label className="flex items-start p-4 min-h-[56px] border-2 border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors touch-manipulation">
                      <input
                        type="radio"
                        name="church_type"
                        value="aci"
                        checked={churchType === 'aci'}
                        onChange={() => handleChurchTypeChange('aci')}
                        className="mt-1 mr-3 h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">Action Chapel International</div>
                        <div className="text-sm text-gray-600 mt-1">Select your ACI branch</div>
                      </div>
                    </label>

                    {/* Other Church Option */}
                    <label className="flex items-start p-4 min-h-[56px] border-2 border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors touch-manipulation">
                      <input
                        type="radio"
                        name="church_type"
                        value="other"
                        checked={churchType === 'other'}
                        onChange={() => handleChurchTypeChange('other')}
                        className="mt-1 mr-3 h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                      />
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">Other</div>
                        <div className="text-sm text-gray-600 mt-1">Enter your church name</div>
                      </div>
                    </label>
                  </div>
                </div>

                {/* ACI Branch Selection - Show when ACI is selected */}
                {churchType === 'aci' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Select Your Branch <span className="text-red-500">*</span>
                    </label>
                    <SearchableBranchSelect
                      branches={branches}
                      value={formData.branch_id}
                      onChange={(branchId) => {
                        setFormData(prev => ({ ...prev, branch_id: branchId }));
                      }}
                      required
                    />
                  </div>
                )}

                {/* Church Name Input - Show when Other is selected */}
                {churchType === 'other' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Church Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      name="church_name"
                      value={formData.church_name}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      placeholder="Enter your church name"
                      required
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Bus Transportation */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Transportation</h3>

              <div className="space-y-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    name="requires_bus"
                    checked={formData.requires_bus}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-700">
                    I need bus transportation to the conference
                  </label>
                </div>

                {formData.requires_bus && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Select Bus Route
                    </label>
                    <SearchableBusRouteSelect
                      busRoutes={busRoutes}
                      value={formData.bus_route_id}
                      onChange={(routeId) => {
                        setFormData(prev => ({ ...prev, bus_route_id: routeId }));
                      }}
                      required
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Special Needs */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Special Needs / Accommodations
              </label>
              <textarea
                name="special_needs"
                value={formData.special_needs}
                onChange={handleInputChange}
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Please let us know if you have any special needs or require accommodations..."
              />
            </div>

            {/* Session Selection (On-site Registration) */}
            {isConferenceOngoing && isWithinVenue && todaysSessions.length > 0 && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <h3 className="text-lg font-semibold text-green-800 mb-2">
                  ✓ You're at the venue!
                </h3>
                <p className="text-sm text-green-700 mb-4">
                  Check in to today's session now (optional):
                </p>
                <div className="space-y-2">
                  <label className="flex items-start p-3 border border-gray-200 rounded-lg hover:bg-white cursor-pointer bg-white">
                    <input
                      type="radio"
                      name="session"
                      value=""
                      checked={selectedSessionId === ''}
                      onChange={() => setSelectedSessionId('')}
                      className="mt-1 mr-3"
                    />
                    <div>
                      <div className="font-medium">Skip for now</div>
                      <div className="text-sm text-gray-600">I'll check in later</div>
                    </div>
                  </label>
                  {todaysSessions.map(session => (
                    <label key={session.id} className="flex items-start p-3 border border-gray-200 rounded-lg hover:bg-white cursor-pointer bg-white">
                      <input
                        type="radio"
                        name="session"
                        value={session.id}
                        checked={selectedSessionId === session.id}
                        onChange={() => setSelectedSessionId(session.id)}
                        className="mt-1 mr-3"
                      />
                      <div>
                        <div className="font-medium">{session.name}</div>
                        <div className="text-sm text-gray-600">
                          {new Date(session.session_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          {session.location && ` • ${session.location}`}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {isConferenceOngoing && locationStatus === 'denied' && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  Location access denied. You can still register, but session check-in will be unavailable.
                </p>
              </div>
            )}

            {/* Submit Button */}
            <div className="pt-4">
              <button
                type="submit"
                disabled={submitting}
                className="w-full min-h-[48px] py-3 px-6 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation"
              >
                {submitting ? 'Registering...' : 'Complete Registration'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
