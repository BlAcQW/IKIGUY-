import { useState } from 'react'
import { Bus, CheckCircle, XCircle, User, MapPin, Clock } from 'lucide-react'
import GreetingAudioPlayer from '../components/GreetingAudioPlayer'
import type { GreetingAudio } from '../lib/api'

interface CheckInResult {
  success: boolean
  user_name: string
  user_phone: string
  bus_route_name: string
  conference_name: string
  check_in_time: string
  greeting_audio?: GreetingAudio
}

export default function BusCheckIn() {
  const [registrationCode, setRegistrationCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CheckInResult | null>(null)
  const [error, setError] = useState('')

  const handleCheckIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch('/api/v1/buses/check-in', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ registration_code: registrationCode })
      })

      const data = await response.json()

      if (response.ok) {
        setResult(data)
        setRegistrationCode('')

        // Auto-clear success message after 5 seconds
        setTimeout(() => {
          setResult(null)
        }, 5000)
      } else {
        setError(data.detail || 'Check-in failed')
      }
    } catch (err: any) {
      setError(err.message || 'Check-in failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
            <Bus className="w-8 h-8 text-purple-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Bus Booking Check-In</h1>
          <p className="text-gray-600">Scan or enter registration codes to check in bus passengers</p>
        </div>

        {/* Registration Code Input Form */}
        <div className="bg-white rounded-xl shadow-lg border p-8 mb-6">
          <form onSubmit={handleCheckIn} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Registration Code
              </label>
              <input
                type="text"
                value={registrationCode}
                onChange={(e) => setRegistrationCode(e.target.value)}
                className="w-full px-4 py-3 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono"
                placeholder="Enter or scan registration code..."
                required
                autoFocus
              />
              <p className="text-xs text-gray-500 mt-2">
                Paste the registration code from the QR code or use a barcode scanner
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || !registrationCode}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-lg"
            >
              {loading ? 'Checking In...' : 'Check In'}
            </button>
          </form>
        </div>

        {/* Success Result */}
        {result && (
          <div className="bg-green-50 border-2 border-green-200 rounded-xl p-6 animate-fade-in">
            <div className="flex items-center gap-4 mb-4">
              <div className="flex-shrink-0">
                <CheckCircle className="w-12 h-12 text-green-600" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-green-900">Check-In Successful!</h3>
                <p className="text-sm text-green-700">Passenger has been checked in for the bus</p>
              </div>
            </div>

            <div className="space-y-3 pl-16">
              <div className="flex items-center gap-3 text-gray-700">
                <User className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="font-semibold">{result.user_name}</p>
                  <p className="text-sm text-gray-600">{result.user_phone}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 text-gray-700">
                <Bus className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="font-semibold">{result.bus_route_name}</p>
                  <p className="text-sm text-gray-600">{result.conference_name}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 text-gray-700">
                <Clock className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="font-semibold">Check-in Time</p>
                  <p className="text-sm text-gray-600">
                    {new Date(result.check_in_time).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>

            {/* Voice Greeting Player */}
            {result.greeting_audio && (
              <div className="mt-4">
                <GreetingAudioPlayer
                  greetingAudio={result.greeting_audio}
                  autoPlay={true}
                />
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6">
            <div className="flex items-center gap-4">
              <XCircle className="w-12 h-12 text-red-600 flex-shrink-0" />
              <div>
                <h3 className="text-xl font-bold text-red-900">Check-In Failed</h3>
                <p className="text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="mt-8 bg-gray-50 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-3">How to check in bus passengers:</h3>
          <ol className="space-y-2 text-sm text-gray-600">
            <li className="flex gap-2">
              <span className="font-bold text-purple-600">1.</span>
              <span>Ask the passenger to show their bus booking QR code from the mobile app or confirmation</span>
            </li>
            <li className="flex gap-2">
              <span className="font-bold text-purple-600">2.</span>
              <span>Scan the QR code with a barcode scanner or manually enter the registration code</span>
            </li>
            <li className="flex gap-2">
              <span className="font-bold text-purple-600">3.</span>
              <span>Verify the passenger's name, phone number, and bus route details</span>
            </li>
            <li className="flex gap-2">
              <span className="font-bold text-purple-600">4.</span>
              <span>The system will automatically record the check-in time and mark the passenger as boarded</span>
            </li>
          </ol>
        </div>

        {/* Stats */}
        <div className="mt-6 grid grid-cols-3 gap-4">
          <div className="bg-white rounded-lg p-4 text-center border">
            <p className="text-2xl font-bold text-gray-900">--</p>
            <p className="text-xs text-gray-600 mt-1">Checked In Today</p>
          </div>
          <div className="bg-white rounded-lg p-4 text-center border">
            <p className="text-2xl font-bold text-gray-900">--</p>
            <p className="text-xs text-gray-600 mt-1">Expected Passengers</p>
          </div>
          <div className="bg-white rounded-lg p-4 text-center border">
            <p className="text-2xl font-bold text-gray-900">--</p>
            <p className="text-xs text-gray-600 mt-1">Boarding Rate</p>
          </div>
        </div>
      </div>
    </div>
  )
}
