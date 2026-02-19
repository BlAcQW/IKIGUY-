import { useState, useEffect } from 'react'
import { X, Users, Search, Download, MapPin, Bus, Calendar } from 'lucide-react'

interface AttendanceReportItem {
  registration_id: string
  user_name: string
  user_phone: string
  user_email: string | null
  branch_name: string | null
  bus_route_name: string | null
  bus_pickup_location: string | null
  sessions_attended: string[]
  total_sessions: number
  first_check_in: string
}

interface AttendanceReportProps {
  conferenceId: string
  conferenceName: string
  onClose: () => void
}

export default function AttendanceReport({ conferenceId, conferenceName, onClose }: AttendanceReportProps) {
  const [report, setReport] = useState<AttendanceReportItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterBranch, setFilterBranch] = useState<string>('')
  const [filterBusRoute, setFilterBusRoute] = useState<string>('')
  const [filterSession, setFilterSession] = useState<string>('')

  useEffect(() => {
    fetchReport()
  }, [conferenceId])

  const fetchReport = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setError('Please login to view attendance report')
      setLoading(false)
      return
    }

    try {
      const response = await fetch(`/api/v1/conferences/${conferenceId}/attendance-report`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setReport(data.report)
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch report' }))
        setError(errorData.detail || 'Failed to fetch attendance report')
      }
    } catch (err) {
      console.error('Failed to fetch attendance report:', err)
      setError('Failed to fetch attendance report')
    } finally {
      setLoading(false)
    }
  }

  // Get unique branches, bus routes, and sessions for filters
  const uniqueBranches = [...new Set(report.map(r => r.branch_name).filter(Boolean))] as string[]
  const uniqueBusRoutes = [...new Set(report.map(r => r.bus_route_name).filter(Boolean))] as string[]
  const uniqueSessions = [...new Set(report.flatMap(r => r.sessions_attended))].sort() as string[]

  // Filter report
  const filteredReport = report.filter(item => {
    const matchesSearch = searchQuery === '' ||
      item.user_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.user_phone.includes(searchQuery) ||
      (item.user_email && item.user_email.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesBranch = filterBranch === '' || item.branch_name === filterBranch
    const matchesBusRoute = filterBusRoute === '' || item.bus_route_name === filterBusRoute
    const matchesSession = filterSession === '' || item.sessions_attended.includes(filterSession)

    return matchesSearch && matchesBranch && matchesBusRoute && matchesSession
  })

  const formatDateTime = (isoString: string) => {
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const exportToCSV = () => {
    const headers = ['Name', 'Phone', 'Email', 'Branch', 'Bus Route', 'Pickup Location', 'Sessions Attended', 'Total Sessions', 'First Check-in']
    const rows = filteredReport.map(item => [
      item.user_name,
      item.user_phone,
      item.user_email || '',
      item.branch_name || '',
      item.bus_route_name || '',
      item.bus_pickup_location || '',
      item.sessions_attended.join('; '),
      item.total_sessions.toString(),
      formatDateTime(item.first_check_in)
    ])

    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `attendance_report_${conferenceName.replace(/\s+/g, '_')}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-6xl mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Attendance Report</h2>
            <p className="text-sm text-gray-500 mt-1">{conferenceName}</p>
            <div className="flex items-center gap-2 mt-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg w-fit">
              <Calendar className="w-4 h-4 text-blue-600" />
              <p className="text-xs text-blue-700 font-medium">
                Shows attendees who checked in to at least one session
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        {/* Summary Stats */}
        <div className="p-4 bg-gray-50 border-b">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-purple-600" />
              <span className="text-sm text-gray-600">
                <strong className="text-gray-900">{filteredReport.length}</strong> attendees
                {filteredReport.length !== report.length && ` (of ${report.length} total)`}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-gray-600">
                <strong className="text-gray-900">{uniqueBranches.length}</strong> branches represented
              </span>
            </div>
            {uniqueBusRoutes.length > 0 && (
              <div className="flex items-center gap-2">
                <Bus className="w-5 h-5 text-green-600" />
                <span className="text-sm text-gray-600">
                  <strong className="text-gray-900">{uniqueBusRoutes.length}</strong> bus routes
                </span>
              </div>
            )}
            {uniqueSessions.length > 0 && (
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-orange-600" />
                <span className="text-sm text-gray-600">
                  <strong className="text-gray-900">{uniqueSessions.length}</strong> sessions
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Filters */}
        <div className="p-4 border-b flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by name, phone, or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          </div>

          {uniqueBranches.length > 0 && (
            <select
              value={filterBranch}
              onChange={(e) => setFilterBranch(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="">All Branches</option>
              {uniqueBranches.sort().map(branch => (
                <option key={branch} value={branch}>{branch}</option>
              ))}
            </select>
          )}

          {uniqueBusRoutes.length > 0 && (
            <select
              value={filterBusRoute}
              onChange={(e) => setFilterBusRoute(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="">All Bus Routes</option>
              {uniqueBusRoutes.sort().map(route => (
                <option key={route} value={route}>{route}</option>
              ))}
            </select>
          )}

          {uniqueSessions.length > 0 && (
            <select
              value={filterSession}
              onChange={(e) => setFilterSession(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="">All Sessions</option>
              {uniqueSessions.map(session => (
                <option key={session} value={session}>{session}</option>
              ))}
            </select>
          )}

          <button
            onClick={exportToCSV}
            disabled={filteredReport.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600">{error}</p>
            </div>
          ) : filteredReport.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">
                {report.length === 0
                  ? 'No attendees have checked into any session yet.'
                  : 'No attendees match your search criteria.'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Phone
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Branch
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Bus Route
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sessions
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      First Check-in
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredReport.map((item) => (
                    <tr key={item.registration_id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div>
                          <div className="font-medium text-gray-900">{item.user_name}</div>
                          {item.user_email && (
                            <div className="text-xs text-gray-500">{item.user_email}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {item.user_phone}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {item.branch_name ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded-full">
                            <MapPin className="w-3 h-3" />
                            {item.branch_name}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-sm">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {item.bus_route_name ? (
                          <div>
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 text-xs rounded-full">
                              <Bus className="w-3 h-3" />
                              {item.bus_route_name}
                            </span>
                            {item.bus_pickup_location && (
                              <div className="text-xs text-gray-500 mt-1">
                                Pickup: {item.bus_pickup_location}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-400 text-sm">-</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div>
                          <span className="inline-flex items-center px-2 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-full">
                            {item.total_sessions} session{item.total_sessions !== 1 ? 's' : ''}
                          </span>
                          <div className="text-xs text-gray-500 mt-1 max-w-[200px] truncate" title={item.sessions_attended.join(', ')}>
                            {item.sessions_attended.join(', ')}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                        {formatDateTime(item.first_check_in)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
