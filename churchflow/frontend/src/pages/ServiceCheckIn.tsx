/**
 * Service Check-in Page
 *
 * Allows both members and visitors to check in to church services.
 * Two modes:
 * 1. Member Check-in: QR scan or phone lookup
 * 2. Visitor Registration + Check-in: Registration form with department interests
 */

import { useState, useEffect } from 'react'
import {
  Users,
  UserPlus,
  QrCode,
  Phone,
  Search,
  Camera,
  CheckCircle,
  XCircle,
  Loader,
  Calendar,
  Clock,
  ChevronDown,
  MapPin,
} from 'lucide-react'
import CameraQRScanner from '../components/CameraQRScanner'
import { getApiUrl } from '../lib/api'

// Types
interface Service {
  id: string
  service_type: string
  service_date: string
  start_time: string
  end_time: string
  sermon_title?: string
  speaker?: string
  status: string
}

interface CheckInResult {
  success: boolean
  user_name: string
  user_phone: string
  service_date: string
  check_in_time: string
  member_status: string
  is_repeat_checkin?: boolean
  message?: string
}

interface VisitorCheckInResult {
  success: boolean
  user_id: string
  user_name: string
  attendance_id: string
  message: string
}

interface MemberSearchResult {
  id: string
  name: string
  full_name: string
  phone: string
  email?: string
  member_status: string
}

type CheckInMode = 'member' | 'visitor'
type MemberCheckInMethod = 'qr' | 'phone' | 'search'

const DEPARTMENTS = [
  { id: 'music', label: 'Music & Worship' },
  { id: 'media', label: 'Media & Tech' },
  { id: 'ushering', label: 'Ushering' },
  { id: 'children', label: "Children's Ministry" },
  { id: 'youth', label: 'Youth Ministry' },
  { id: 'hospitality', label: 'Hospitality' },
  { id: 'evangelism', label: 'Evangelism' },
  { id: 'prayer', label: 'Prayer Ministry' },
]

export default function ServiceCheckIn() {
  const [mode, setMode] = useState<CheckInMode>('member')
  const [memberMethod, setMemberMethod] = useState<MemberCheckInMethod>('qr')

  // Service selection
  const [services, setServices] = useState<Service[]>([])
  const [selectedService, setSelectedService] = useState<Service | null>(null)
  const [loadingServices, setLoadingServices] = useState(false)

  // Member check-in state
  const [qrCode, setQrCode] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<MemberSearchResult[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [showScanner, setShowScanner] = useState(false)
  const [checkInLoading, setCheckInLoading] = useState(false)
  const [checkInResult, setCheckInResult] = useState<CheckInResult | null>(null)
  const [checkInError, setCheckInError] = useState('')

  // Visitor registration state
  const [visitorName, setVisitorName] = useState('')
  const [visitorPhone, setVisitorPhone] = useState('')
  const [visitorEmail, setVisitorEmail] = useState('')
  const [visitorChurch, setVisitorChurch] = useState('')
  const [selectedDepartments, setSelectedDepartments] = useState<string[]>([])
  const [visitorLoading, setVisitorLoading] = useState(false)
  const [visitorResult, setVisitorResult] = useState<VisitorCheckInResult | null>(null)
  const [visitorError, setVisitorError] = useState('')

  // Fetch upcoming services on mount
  useEffect(() => {
    fetchUpcomingServices()
  }, [])

  const fetchUpcomingServices = async () => {
    setLoadingServices(true)
    try {
      const token = localStorage.getItem('access_token')
      const today = new Date().toISOString().split('T')[0]
      const weekLater = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]

      const response = await fetch(
        getApiUrl(`services?start_date=${today}&end_date=${weekLater}&status=upcoming`),
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (response.ok) {
        const data = await response.json()
        setServices(data)
        // Auto-select today's service if available
        const todayService = data.find((s: Service) => s.service_date.startsWith(today))
        if (todayService) {
          setSelectedService(todayService)
        }
      }
    } catch (err) {
      console.error('Failed to fetch services:', err)
    } finally {
      setLoadingServices(false)
    }
  }

  // Member check-in handlers
  const handleQRScan = async (code: string) => {
    setQrCode(code)
    await performMemberCheckIn(code, 'qr_scan')
  }

  const handlePhoneCheckIn = async () => {
    if (!phoneNumber.trim()) return
    // Normalize phone number to +233 format
    const normalizedPhone = phoneNumber.startsWith('+233')
      ? phoneNumber
      : phoneNumber.startsWith('0')
      ? '+233' + phoneNumber.slice(1)
      : '+233' + phoneNumber

    await performMemberCheckIn(normalizedPhone, 'phone_lookup')
  }

  const handleMemberSelect = async (member: MemberSearchResult) => {
    await performMemberCheckIn(member.id, 'manual_search')
  }

  const performMemberCheckIn = async (identifier: string, method: string) => {
    if (!selectedService) {
      setCheckInError('Please select a service first')
      return
    }

    setCheckInLoading(true)
    setCheckInError('')
    setCheckInResult(null)

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(getApiUrl(`services/${selectedService.id}/check-in`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          identifier, // Can be QR code, phone number, or user_id
          check_in_method: method,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setCheckInResult(data)
        // Reset form
        setQrCode('')
        setPhoneNumber('')
        setSearchQuery('')
        setSearchResults([])
      } else {
        setCheckInError(data.detail || 'Check-in failed')
      }
    } catch (err: any) {
      console.error('Check-in error:', err)
      setCheckInError('Network error. Please try again.')
    } finally {
      setCheckInLoading(false)
    }
  }

  const searchMembers = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }

    setSearchLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(getApiUrl(`users/search?q=${encodeURIComponent(searchQuery)}`), {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setSearchResults(data.results || [])
      }
    } catch (err) {
      console.error('Search error:', err)
    } finally {
      setSearchLoading(false)
    }
  }

  // Visitor registration handler
  const handleVisitorRegistration = async () => {
    if (!selectedService) {
      setVisitorError('Please select a service first')
      return
    }

    if (!visitorName.trim() || !visitorPhone.trim()) {
      setVisitorError('Name and phone number are required')
      return
    }

    setVisitorLoading(true)
    setVisitorError('')
    setVisitorResult(null)

    try {
      const token = localStorage.getItem('access_token')
      // Normalize phone number
      const normalizedPhone = visitorPhone.startsWith('+233')
        ? visitorPhone
        : visitorPhone.startsWith('0')
        ? '+233' + visitorPhone.slice(1)
        : '+233' + visitorPhone

      const response = await fetch(
        getApiUrl(`services/${selectedService.id}/register-and-check-in`),
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            name: visitorName,
            phone: normalizedPhone,
            email: visitorEmail || undefined,
            church_name: visitorChurch || undefined,
            department_interests: selectedDepartments,
          }),
        }
      )

      const data = await response.json()

      if (response.ok) {
        setVisitorResult(data)
        // Reset form
        setVisitorName('')
        setVisitorPhone('')
        setVisitorEmail('')
        setVisitorChurch('')
        setSelectedDepartments([])
      } else {
        setVisitorError(data.detail || 'Registration failed')
      }
    } catch (err: any) {
      console.error('Visitor registration error:', err)
      setVisitorError('Network error. Please try again.')
    } finally {
      setVisitorLoading(false)
    }
  }

  const toggleDepartment = (deptId: string) => {
    setSelectedDepartments((prev) =>
      prev.includes(deptId) ? prev.filter((d) => d !== deptId) : [...prev, deptId]
    )
  }

  const formatServiceType = (type: string) => {
    const labels: Record<string, string> = {
      sunday_8am: 'Sunday 8:00 AM',
      sunday_10am: 'Sunday 10:00 AM',
      midweek: 'Midweek Service',
      special: 'Special Service',
    }
    return labels[type] || type
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="w-6 h-6 text-purple-600" />
            Service Check-in
          </h1>
          <p className="text-sm text-gray-500 mt-1">Check in members or register new visitors</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Service Selection */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Select Service</label>
          {loadingServices ? (
            <div className="flex items-center justify-center py-4">
              <Loader className="w-5 h-5 animate-spin text-purple-600" />
            </div>
          ) : (
            <div className="relative">
              <select
                value={selectedService?.id || ''}
                onChange={(e) => {
                  const service = services.find((s) => s.id === e.target.value)
                  setSelectedService(service || null)
                }}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none bg-white pr-10"
              >
                <option value="">-- Select a service --</option>
                {services.map((service) => (
                  <option key={service.id} value={service.id}>
                    {new Date(service.service_date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      month: 'short',
                      day: 'numeric',
                    })}{' '}
                    - {formatServiceType(service.service_type)}
                    {service.sermon_title ? ` - ${service.sermon_title}` : ''}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
            </div>
          )}

          {selectedService && (
            <div className="mt-4 p-4 bg-purple-50 rounded-lg">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2 text-gray-700">
                  <Calendar className="w-4 h-4 text-purple-600" />
                  <span>
                    {new Date(selectedService.service_date).toLocaleDateString('en-US', {
                      weekday: 'long',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-gray-700">
                  <Clock className="w-4 h-4 text-purple-600" />
                  <span>
                    {selectedService.start_time} - {selectedService.end_time}
                  </span>
                </div>
              </div>
              {selectedService.speaker && (
                <p className="text-sm text-gray-600 mt-2">
                  Speaker: <span className="font-medium">{selectedService.speaker}</span>
                </p>
              )}
            </div>
          )}
        </div>

        {/* Mode Toggle */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-2 mb-6 flex gap-2">
          <button
            onClick={() => setMode('member')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors ${
              mode === 'member'
                ? 'bg-purple-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Users className="w-5 h-5" />
            <span>Member Check-in</span>
          </button>
          <button
            onClick={() => setMode('visitor')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors ${
              mode === 'visitor'
                ? 'bg-purple-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            <UserPlus className="w-5 h-5" />
            <span>Register Visitor</span>
          </button>
        </div>

        {/* Member Check-in Section */}
        {mode === 'member' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            {/* Method Selection */}
            <div className="flex gap-2 mb-6">
              <button
                onClick={() => setMemberMethod('qr')}
                className={`flex-1 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                  memberMethod === 'qr'
                    ? 'bg-purple-100 text-purple-700 border-2 border-purple-300'
                    : 'bg-gray-50 text-gray-600 border border-gray-200'
                }`}
              >
                <QrCode className="w-4 h-4 mx-auto mb-1" />
                QR Code
              </button>
              <button
                onClick={() => setMemberMethod('phone')}
                className={`flex-1 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                  memberMethod === 'phone'
                    ? 'bg-purple-100 text-purple-700 border-2 border-purple-300'
                    : 'bg-gray-50 text-gray-600 border border-gray-200'
                }`}
              >
                <Phone className="w-4 h-4 mx-auto mb-1" />
                Phone
              </button>
              <button
                onClick={() => setMemberMethod('search')}
                className={`flex-1 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                  memberMethod === 'search'
                    ? 'bg-purple-100 text-purple-700 border-2 border-purple-300'
                    : 'bg-gray-50 text-gray-600 border border-gray-200'
                }`}
              >
                <Search className="w-4 h-4 mx-auto mb-1" />
                Search
              </button>
            </div>

            {/* QR Code Method */}
            {memberMethod === 'qr' && (
              <div>
                <button
                  onClick={() => setShowScanner(true)}
                  disabled={!selectedService}
                  className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
                >
                  <Camera className="w-5 h-5" />
                  <span>Open Camera to Scan QR Code</span>
                </button>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  Members can show their registration QR code
                </p>
              </div>
            )}

            {/* Phone Lookup Method */}
            {memberMethod === 'phone' && (
              <div>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handlePhoneCheckIn()}
                    placeholder="Enter phone number (e.g., 0244123456)"
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
                <button
                  onClick={handlePhoneCheckIn}
                  disabled={!selectedService || !phoneNumber.trim() || checkInLoading}
                  className="w-full mt-3 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
                >
                  {checkInLoading ? (
                    <Loader className="w-5 h-5 animate-spin mx-auto" />
                  ) : (
                    'Check In'
                  )}
                </button>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  Ghana format: +233 or 0244123456
                </p>
              </div>
            )}

            {/* Search Method */}
            {memberMethod === 'search' && (
              <div>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value)
                      if (e.target.value.length >= 3) {
                        searchMembers()
                      } else {
                        setSearchResults([])
                      }
                    }}
                    placeholder="Search by name..."
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>

                {/* Search Results */}
                {searchLoading && (
                  <div className="mt-3 p-4 text-center">
                    <Loader className="w-5 h-5 animate-spin mx-auto text-purple-600" />
                  </div>
                )}

                {searchResults.length > 0 && (
                  <div className="mt-3 border border-gray-200 rounded-lg overflow-hidden max-h-64 overflow-y-auto">
                    {searchResults.map((member) => (
                      <button
                        key={member.id}
                        onClick={() => handleMemberSelect(member)}
                        disabled={checkInLoading}
                        className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0 disabled:opacity-50"
                      >
                        <div className="font-medium text-gray-900">
                          {member.name || member.full_name}
                        </div>
                        <div className="text-sm text-gray-500">{member.phone}</div>
                        {member.email && (
                          <div className="text-xs text-gray-400">{member.email}</div>
                        )}
                      </button>
                    ))}
                  </div>
                )}

                {searchQuery.length >= 3 && !searchLoading && searchResults.length === 0 && (
                  <div className="mt-3 p-4 bg-gray-50 rounded-lg text-center text-sm text-gray-600">
                    No members found. Try a different search term.
                  </div>
                )}
              </div>
            )}

            {/* Check-in Error */}
            {checkInError && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-red-900">Check-in Failed</p>
                  <p className="text-sm text-red-700 mt-1">{checkInError}</p>
                </div>
              </div>
            )}

            {/* Check-in Success */}
            {checkInResult && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start gap-3 mb-3">
                  <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="font-semibold text-green-900 text-lg">
                      {checkInResult.is_repeat_checkin
                        ? 'Already Checked In'
                        : 'Check-in Successful!'}
                    </p>
                    <p className="text-green-700 mt-1">{checkInResult.user_name}</p>
                    <p className="text-sm text-green-600">{checkInResult.user_phone}</p>
                  </div>
                </div>
                <div className="text-sm text-green-700">
                  <p>
                    Status:{' '}
                    <span className="font-medium capitalize">
                      {checkInResult.member_status.replace(/_/g, ' ')}
                    </span>
                  </p>
                  <p>
                    Time:{' '}
                    {new Date(checkInResult.check_in_time).toLocaleTimeString('en-US', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                  {checkInResult.message && (
                    <p className="mt-2 text-xs">{checkInResult.message}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Visitor Registration Section */}
        {mode === 'visitor' && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Visitor Information</h3>

            <div className="space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Full Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={visitorName}
                  onChange={(e) => setVisitorName(e.target.value)}
                  placeholder="John Doe"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              {/* Phone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone Number <span className="text-red-500">*</span>
                </label>
                <input
                  type="tel"
                  value={visitorPhone}
                  onChange={(e) => setVisitorPhone(e.target.value)}
                  placeholder="0244123456"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">Ghana format: +233 or 0244123456</p>
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email (Optional)
                </label>
                <input
                  type="email"
                  value={visitorEmail}
                  onChange={(e) => setVisitorEmail(e.target.value)}
                  placeholder="john@example.com"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              {/* Church Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Home Church (Optional)
                </label>
                <input
                  type="text"
                  value={visitorChurch}
                  onChange={(e) => setVisitorChurch(e.target.value)}
                  placeholder="e.g., Grace Chapel, Accra"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              {/* Department Interests */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Interested in Serving? (Optional)
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {DEPARTMENTS.map((dept) => (
                    <button
                      key={dept.id}
                      onClick={() => toggleDepartment(dept.id)}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        selectedDepartments.includes(dept.id)
                          ? 'bg-purple-100 text-purple-700 border-2 border-purple-300'
                          : 'bg-gray-50 text-gray-600 border border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      {dept.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <button
                onClick={handleVisitorRegistration}
                disabled={
                  !selectedService ||
                  !visitorName.trim() ||
                  !visitorPhone.trim() ||
                  visitorLoading
                }
                className="w-full px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors flex items-center justify-center gap-2"
              >
                {visitorLoading ? (
                  <Loader className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <UserPlus className="w-5 h-5" />
                    <span>Register & Check In</span>
                  </>
                )}
              </button>
            </div>

            {/* Visitor Error */}
            {visitorError && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-red-900">Registration Failed</p>
                  <p className="text-sm text-red-700 mt-1">{visitorError}</p>
                </div>
              </div>
            )}

            {/* Visitor Success */}
            {visitorResult && (
              <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start gap-3 mb-3">
                  <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="font-semibold text-green-900 text-lg">Welcome!</p>
                    <p className="text-green-700 mt-1">{visitorResult.user_name}</p>
                    <p className="text-sm text-green-600 mt-2">{visitorResult.message}</p>
                  </div>
                </div>
                <div className="mt-3 p-3 bg-white rounded border border-green-200">
                  <p className="text-xs text-gray-600">
                    You've been successfully registered and checked in. We're glad to have you with
                    us today!
                  </p>
                  {selectedDepartments.length > 0 && (
                    <p className="text-xs text-gray-600 mt-2">
                      Our team will reach out to you about the departments you're interested in.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* QR Scanner Modal */}
      {showScanner && <CameraQRScanner onScan={handleQRScan} onClose={() => setShowScanner(false)} />}
    </div>
  )
}
