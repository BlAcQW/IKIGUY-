/**
 * Attendance Analytics Dashboard
 *
 * Comprehensive analytics for service attendance tracking.
 * Displays trends, member vs visitor breakdown, department interests, and growth metrics.
 */

import { useState, useEffect } from 'react'
import { Users, TrendingUp, Calendar, PieChart as PieChartIcon, Activity, Filter } from 'lucide-react'
import { getApiUrl } from '../config/api-config'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface AttendanceStats {
  total_services: number
  total_attendance: number
  average_attendance: number
  member_count: number
  visitor_count: number
  first_timer_count: number
  returning_visitor_count: number
  growth_rate: number
  attendance_by_service_type: {
    service_type: string
    count: number
    avg_attendance: number
  }[]
  attendance_trend: {
    date: string
    total: number
    members: number
    visitors: number
  }[]
  department_interests: {
    department: string
    count: number
  }[]
  spiritual_stage_breakdown: {
    stage: string
    count: number
  }[]
}

const COLORS = ['#9333ea', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#6366f1', '#8b5cf6']

export default function AttendanceAnalytics() {
  const [stats, setStats] = useState<AttendanceStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [dateRange, setDateRange] = useState('30d')
  const [selectedBranch, setSelectedBranch] = useState<string>('')
  const [branches, setBranches] = useState<any[]>([])

  useEffect(() => {
    fetchBranches()
  }, [])

  useEffect(() => {
    fetchStats()
  }, [dateRange, selectedBranch])

  const fetchBranches = async () => {
    const token = localStorage.getItem('access_token')
    try {
      const response = await fetch(getApiUrl('branches'), {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setBranches(data)
      }
    } catch (err) {
      console.error('Failed to fetch branches:', err)
    }
  }

  const fetchStats = async () => {
    setLoading(true)
    const token = localStorage.getItem('access_token')

    try {
      const params = new URLSearchParams()
      params.append('period', dateRange)
      if (selectedBranch) params.append('branch_id', selectedBranch)

      const response = await fetch(getApiUrl(`analytics/attendance?${params.toString()}`), {
        headers: { Authorization: `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Failed to fetch attendance stats:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatServiceType = (type: string) => {
    const labels: Record<string, string> = {
      sunday_8am: 'Sunday 8AM',
      sunday_10am: 'Sunday 10AM',
      midweek: 'Midweek',
      special: 'Special'
    }
    return labels[type] || type
  }

  const formatDepartment = (dept: string) => {
    return dept.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No attendance data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Attendance Analytics</h1>
          <p className="text-gray-600 mt-1">Track service attendance trends and member engagement</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm">
        <div className="flex items-center gap-4">
          <Filter className="w-5 h-5 text-gray-400" />

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Time Period</label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="w-full p-2 border rounded-lg"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="6m">Last 6 Months</option>
              <option value="1y">Last Year</option>
            </select>
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Branch</label>
            <select
              value={selectedBranch}
              onChange={(e) => setSelectedBranch(e.target.value)}
              className="w-full p-2 border rounded-lg"
            >
              <option value="">All Branches</option>
              {branches.map(branch => (
                <option key={branch.id} value={branch.id}>{branch.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Services</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_services}</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <Calendar className="w-8 h-8 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Attendance</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total_attendance}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Users className="w-8 h-8 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Average per Service</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">
                {Math.round(stats.average_attendance)}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-lg">
              <Activity className="w-8 h-8 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Growth Rate</p>
              <p className={`text-3xl font-bold mt-2 ${
                stats.growth_rate >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {stats.growth_rate >= 0 ? '+' : ''}{stats.growth_rate.toFixed(1)}%
              </p>
            </div>
            <div className={`p-3 rounded-lg ${
              stats.growth_rate >= 0 ? 'bg-green-100' : 'bg-red-100'
            }`}>
              <TrendingUp className={`w-8 h-8 ${
                stats.growth_rate >= 0 ? 'text-green-600' : 'text-red-600'
              }`} />
            </div>
          </div>
        </div>
      </div>

      {/* Member vs Visitor Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Member vs Visitor Breakdown</h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Members</span>
                <span className="text-sm font-bold text-gray-900">
                  {stats.member_count} ({((stats.member_count / stats.total_attendance) * 100).toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full"
                  style={{ width: `${(stats.member_count / stats.total_attendance) * 100}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Visitors</span>
                <span className="text-sm font-bold text-gray-900">
                  {stats.visitor_count} ({((stats.visitor_count / stats.total_attendance) * 100).toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${(stats.visitor_count / stats.total_attendance) * 100}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">First Timers</span>
                <span className="text-sm font-bold text-gray-900">
                  {stats.first_timer_count} ({((stats.first_timer_count / stats.total_attendance) * 100).toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{ width: `${(stats.first_timer_count / stats.total_attendance) * 100}%` }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Returning Visitors</span>
                <span className="text-sm font-bold text-gray-900">
                  {stats.returning_visitor_count} ({((stats.returning_visitor_count / stats.total_attendance) * 100).toFixed(1)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-amber-600 h-2 rounded-full"
                  style={{ width: `${(stats.returning_visitor_count / stats.total_attendance) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* Spiritual Stage Breakdown */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Spiritual Stage Distribution</h3>
          {stats.spiritual_stage_breakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={stats.spiritual_stage_breakdown}
                  dataKey="count"
                  nameKey="stage"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={(entry) => `${entry.stage}: ${entry.count}`}
                >
                  {stats.spiritual_stage_breakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-center text-gray-500 py-12">No data available</p>
          )}
        </div>
      </div>

      {/* Attendance Trend Chart */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Attendance Trend</h3>
        {stats.attendance_trend.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats.attendance_trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="total" stroke="#9333ea" strokeWidth={2} name="Total" />
              <Line type="monotone" dataKey="members" stroke="#3b82f6" strokeWidth={2} name="Members" />
              <Line type="monotone" dataKey="visitors" stroke="#10b981" strokeWidth={2} name="Visitors" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-center text-gray-500 py-12">No trend data available</p>
        )}
      </div>

      {/* Service Type Breakdown */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Attendance by Service Type</h3>
        {stats.attendance_by_service_type.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats.attendance_by_service_type}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="service_type" tickFormatter={formatServiceType} />
              <YAxis />
              <Tooltip labelFormatter={formatServiceType} />
              <Legend />
              <Bar dataKey="count" fill="#9333ea" name="Total Services" />
              <Bar dataKey="avg_attendance" fill="#3b82f6" name="Avg Attendance" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-center text-gray-500 py-12">No data available</p>
        )}
      </div>

      {/* Department Interests */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Popular Department Interests</h3>
        {stats.department_interests.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {stats.department_interests.map((dept, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 text-center">
                <p className="text-sm font-medium text-gray-700">{formatDepartment(dept.department)}</p>
                <p className="text-2xl font-bold text-purple-600 mt-2">{dept.count}</p>
                <p className="text-xs text-gray-500">interested</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-gray-500 py-12">No department data available</p>
        )}
      </div>
    </div>
  )
}
