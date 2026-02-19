import { useState, useEffect } from 'react'
import { Bus, MapPin, Users, CheckCircle, AlertCircle, X, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'
import axios from 'axios'

const API_BASE = '/api/v1'

interface BusRoute {
  id: string
  conference_id?: string
  name: string
  route_name: string
  pickup_location: string
  departure_location: string
  departure_time?: string | null
  arrival_time?: string | null
  capacity?: number
  registered_count: number
  status: string
  gate_number?: string | null
}

interface BookingForm {
  user_name: string
  user_phone: string
  user_email: string
}

interface BookingResult {
  registration_code: string
  qr_code: string
  user_name: string
  user_phone: string
  bus_route_name: string
  conference_name?: string
}

export default function BusBooking() {
  const [busRoutes, setBusRoutes] = useState<BusRoute[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [bookingResult, setBookingResult] = useState<BookingResult | null>(null)
  const [selectedRoute, setSelectedRoute] = useState<BusRoute | null>(null)
  const [showModal, setShowModal] = useState(false)

  const [formData, setFormData] = useState<BookingForm>({
    user_name: '',
    user_phone: '',
    user_email: ''
  })

  useEffect(() => {
    loadBusRoutes()
  }, [])

  const loadBusRoutes = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE}/buses/routes`)
      setBusRoutes(response.data.filter((route: BusRoute) =>
        !route.status || route.status === 'active'
      ))
    } catch (err) {
      console.error('Failed to load bus routes:', err)
      setError('Failed to load bus routes')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectRoute = (route: BusRoute) => {
    setSelectedRoute(route)
    setShowModal(true)
    setError(null)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setSelectedRoute(null)
    setError(null)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.user_name || !formData.user_phone || !selectedRoute) {
      setError('Please fill in all required fields')
      return
    }

    try {
      setSubmitting(true)
      setError(null)

      const bookingResponse = await axios.post(`${API_BASE}/buses/register`, {
        bus_route_id: selectedRoute.id,
        user_name: formData.user_name,
        user_phone: formData.user_phone,
        user_email: formData.user_email || null
      })

      if (bookingResponse.data) {
        setBookingResult({
          registration_code: bookingResponse.data.registration_code,
          qr_code: bookingResponse.data.qr_code,
          user_name: bookingResponse.data.user_name,
          user_phone: bookingResponse.data.user_phone,
          bus_route_name: bookingResponse.data.bus_route_name,
          conference_name: bookingResponse.data.conference_name
        })
        setSuccess(true)
        setShowModal(false)

        // Reset form
        setFormData({
          user_name: '',
          user_phone: '',
          user_email: ''
        })
      }
    } catch (err: any) {
      console.error('Booking error:', err)
      setError(err.response?.data?.detail || 'Failed to book bus seat. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading bus routes...</p>
        </div>
      </div>
    )
  }

  if (success && bookingResult) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-12 px-4">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center">
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
                <CheckCircle className="h-10 w-10 text-green-600" />
              </div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Booking Successful!</h2>
              <p className="text-gray-600 mb-6">Your bus seat has been reserved</p>

              {/* QR Code */}
              <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-6 mb-6">
                <h3 className="font-semibold text-gray-900 mb-4">Your Bus Boarding Pass</h3>
                <div className="bg-white rounded-lg p-4 inline-block mx-auto shadow-md">
                  <img
                    src={bookingResult.qr_code}
                    alt="Bus Boarding QR Code"
                    className="w-48 h-48 sm:w-64 sm:h-64 mx-auto"
                  />
                </div>
                <p className="text-sm text-gray-600 mt-3">
                  Present this QR code when boarding the bus
                </p>
                <div className="mt-2 font-mono text-sm text-gray-700 bg-white rounded px-3 py-2 inline-block">
                  {bookingResult.registration_code}
                </div>
              </div>

              {/* Booking Details */}
              <div className="bg-blue-50 rounded-xl p-6 mb-6 text-left">
                <h3 className="font-semibold text-gray-900 mb-3">Booking Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Name:</span>
                    <span className="font-medium">{bookingResult.user_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Phone:</span>
                    <span className="font-medium">{bookingResult.user_phone}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Bus Route:</span>
                    <span className="font-medium">{bookingResult.bus_route_name}</span>
                  </div>
                  {bookingResult.conference_name && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Conference:</span>
                      <span className="font-medium">{bookingResult.conference_name}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Important Note */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                <p className="text-sm text-yellow-800">
                  <strong>Important:</strong> Please save or screenshot this QR code. You will need it to board the bus.
                </p>
              </div>

              <div className="flex gap-4 justify-center">
                <button
                  onClick={() => {
                    setSuccess(false)
                    setBookingResult(null)
                    setSelectedRoute(null)
                  }}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Book Another Seat
                </button>
                <Link
                  to="/"
                  className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Return Home
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Bus className="w-7 h-7 sm:w-8 sm:h-8 text-blue-600" />
                Book Bus Transportation
              </h1>
              <p className="text-gray-600 mt-2 text-sm sm:text-base">Select a bus route and reserve your seat</p>
            </div>
            <Link
              to="/"
              className="text-blue-600 hover:text-blue-700 font-medium text-sm sm:text-base"
            >
              ← Back
            </Link>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {busRoutes.length === 0 ? (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <Bus className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-gray-500 text-lg">No bus routes available at the moment</p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {busRoutes.map(route => (
              <div
                key={route.id}
                className="bg-white border border-gray-200 rounded-xl p-5 sm:p-6 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="mb-4">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-lg font-bold text-gray-900 leading-tight">
                      {route.name || route.route_name}
                    </h3>
                    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 whitespace-nowrap ml-2">
                      AVAILABLE
                    </span>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-gray-600">
                      <MapPin className="w-4 h-4 flex-shrink-0" />
                      <span className="text-sm">{route.pickup_location || route.departure_location}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                      <Users className="w-4 h-4 flex-shrink-0" />
                      <span className="text-sm">
                        {route.registered_count} registered
                        {route.capacity && ` / ${route.capacity} capacity`}
                      </span>
                    </div>
                    {route.departure_time && (
                      <div className="flex items-center gap-2 text-gray-600">
                        <Clock className="w-4 h-4 flex-shrink-0" />
                        <span className="text-sm">
                          {new Date(route.departure_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    )}
                    {route.gate_number && (
                      <div className="flex items-center gap-2 text-gray-600">
                        <span className="text-sm font-medium">Gate {route.gate_number}</span>
                      </div>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => handleSelectRoute(route)}
                  className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                >
                  Select & Book
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Booking Modal */}
      {showModal && selectedRoute && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Book Your Seat</h2>
                <p className="text-sm text-gray-500 mt-0.5">{selectedRoute.name || selectedRoute.route_name}</p>
              </div>
              <button
                onClick={handleCloseModal}
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Route Info */}
            <div className="px-6 py-4 bg-blue-50 border-b border-blue-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                  <Bus className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{selectedRoute.name || selectedRoute.route_name}</p>
                  <p className="text-sm text-gray-600">{selectedRoute.pickup_location || selectedRoute.departure_location}</p>
                </div>
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <p className="text-red-800 text-sm">{error}</p>
                </div>
              )}

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
                  autoFocus
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                  placeholder="Enter your full name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone Number <span className="text-red-500">*</span>
                </label>
                <input
                  type="tel"
                  name="user_phone"
                  value={formData.user_phone}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                  placeholder="+233XXXXXXXXX"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email <span className="text-gray-400">(Optional)</span>
                </label>
                <input
                  type="email"
                  name="user_email"
                  value={formData.user_email}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-base"
                  placeholder="email@example.com"
                />
              </div>

              <div className="pt-4 flex gap-3">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="flex-1 py-3 px-4 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Booking...' : 'Confirm Booking'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
