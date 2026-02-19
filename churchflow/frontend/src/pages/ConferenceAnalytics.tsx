/**
 * Conference Analytics Page
 * 
 * Displays comprehensive analytics for conference attendees including:
 * - Breakdown by branch (with country distribution)
 * - Breakdown by country (with branch distribution)
 * - Breakdown by session (check-in statistics)
 * - Top percentages for each grouping
 * - Search functionality for country and branch
 */

import { useState, useEffect } from 'react'
import { Search, BarChart3, Users, MapPin, Calendar, TrendingUp, Filter, X, Sparkles, Loader2, ChevronUp, ChevronDown, ChevronsUpDown, Copy, Check } from 'lucide-react'
import { API_BASE_URL } from '../config/api-config'

interface BranchAnalytics {
  branch_id: string
  branch_name: string
  branch_location: string | null
  branch_region: string | null
  total_registrations: number
  percentage: number
  checked_in_count: number
  checked_in_percentage: number
  countries: Record<string, number>
}

interface CountryAnalytics {
  country_code: string
  country_name: string
  total_registrations: number
  percentage: number
  checked_in_count: number
  checked_in_percentage: number
  branches: Record<string, number>
}

interface SessionAnalytics {
  session_id: string
  session_name: string
  day_number: number
  day_label: string
  total_checked_in: number
  percentage: number
  unique_attendees: number
}

interface ConferenceAnalytics {
  conference_id: string
  conference_name: string
  total_registrations: number
  total_checked_in: number
  by_branch: BranchAnalytics[]
  by_country: CountryAnalytics[]
  by_session: SessionAnalytics[]
  top_branches: BranchAnalytics[]
  top_countries: CountryAnalytics[]
  top_sessions: SessionAnalytics[]
}

interface Conference {
  id: string
  name: string
  start_date: string
  end_date: string
}

interface ConferenceAnalyticsProps {
  /** Optional conference ID to lock analytics to (e.g., from ConferenceDetail). */
  conferenceId?: string
}

export default function ConferenceAnalytics({ conferenceId }: ConferenceAnalyticsProps) {
  const [conferences, setConferences] = useState<Conference[]>([])
  const [selectedConferenceId, setSelectedConferenceId] = useState<string>(conferenceId || '')
  const [analytics, setAnalytics] = useState<ConferenceAnalytics | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'branch' | 'country' | 'session'>('branch')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchType, setSearchType] = useState<'country' | 'branch'>('country')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  const [summaryType, setSummaryType] = useState<string>('overview')
  const [customPrompt, setCustomPrompt] = useState<string>('')
  const [generatingSummary, setGeneratingSummary] = useState(false)
  const [summary, setSummary] = useState<string | null>(null)
  const [summaryError, setSummaryError] = useState<string | null>(null)
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null)
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null)
  const [selectedBranch, setSelectedBranch] = useState<string | null>(null)
  const [branchAttendees, setBranchAttendees] = useState<any[]>([])
  const [loadingAttendees, setLoadingAttendees] = useState(false)
  const [copiedSummary, setCopiedSummary] = useState(false)

  useEffect(() => {
    fetchConferences()
  }, [])

  useEffect(() => {
    if (selectedConferenceId) {
      fetchAnalytics(selectedConferenceId)
      // Reset selections when conference changes
      setSelectedCountry(null)
      setSelectedBranch(null)
      setBranchAttendees([])
    }
  }, [selectedConferenceId])

  // Reset sort when switching tabs
  useEffect(() => {
    setSortConfig(null)
    setSelectedCountry(null)
    setSelectedBranch(null)
    setBranchAttendees([])
  }, [activeTab])

  const fetchConferences = async () => {
    // When a specific conferenceId is provided, we skip list loading
    // and let the parent control which conference is active.
    if (conferenceId) {
      setConferences([])
      setSelectedConferenceId(conferenceId)
      return
    }

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch('/api/v1/conferences', {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      })
      if (response.ok) {
        const data = await response.json()
        setConferences(data)
        if (data.length > 0 && !selectedConferenceId) {
          setSelectedConferenceId(data[0].id)
        }
      }
    } catch (err) {
      console.error('Failed to fetch conferences:', err)
    }
  }

  const fetchAnalytics = async (conferenceId: string) => {
    setLoading(true)
    setError(null)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setError('Please login to view analytics')
        setLoading(false)
        return
      }

      const response = await fetch(
        `${API_BASE_URL}/api/v1/conferences/${conferenceId}/analytics`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setAnalytics(data)
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to load analytics' }))
        setError(errorData.detail || 'Failed to load analytics')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!selectedConferenceId || !searchQuery.trim()) {
      return
    }

    setSearching(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return

      const params = new URLSearchParams()
      if (searchType === 'country') {
        params.append('country', searchQuery)
      } else {
        params.append('branch', searchQuery)
      }

      const response = await fetch(
        `${API_BASE_URL}/api/v1/conferences/${selectedConferenceId}/analytics/search?${params}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setSearchResults(data.registrations || [])
      } else {
        setSearchResults([])
      }
    } catch (err) {
      console.error('Search failed:', err)
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  const clearSearch = () => {
    setSearchQuery('')
    setSearchResults([])
  }

  const generateSummary = async () => {
    if (!selectedConferenceId || !analytics) {
      return
    }

    setGeneratingSummary(true)
    setSummaryError(null)
    setSummary(null)

    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setSummaryError('Please login to generate summaries')
        setGeneratingSummary(false)
        return
      }

      const response = await fetch(
        `${API_BASE_URL}/api/v1/conferences/${selectedConferenceId}/analytics/summary`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            summary_type: summaryType,
            custom_prompt: summaryType === 'custom' ? customPrompt : undefined
          })
        }
      )

      if (response.ok) {
        const data = await response.json()
        setSummary(data.summary)
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to generate summary' }))
        setSummaryError(errorData.detail || 'Failed to generate summary')
      }
    } catch (err: any) {
      setSummaryError(err.message || 'Failed to generate summary')
    } finally {
      setGeneratingSummary(false)
    }
  }

  const copySummaryToClipboard = async () => {
    if (!summary) return

    try {
      await navigator.clipboard.writeText(summary)
      setCopiedSummary(true)

      // Reset copied state after 2 seconds
      setTimeout(() => {
        setCopiedSummary(false)
      }, 2000)
    } catch (err) {
      console.error('Failed to copy summary:', err)
    }
  }

  const getFilteredData = () => {
    if (!analytics) return { branches: [], countries: [], sessions: [] }

    const query = searchQuery.toLowerCase()
    
    if (!query) {
      return {
        branches: analytics.by_branch,
        countries: analytics.by_country,
        sessions: analytics.by_session
      }
    }

    return {
      branches: analytics.by_branch.filter(b =>
        b.branch_name.toLowerCase().includes(query) ||
        b.branch_location?.toLowerCase().includes(query) ||
        b.branch_region?.toLowerCase().includes(query)
      ),
      countries: analytics.by_country.filter(c =>
        c.country_name.toLowerCase().includes(query) ||
        c.country_code.toLowerCase().includes(query)
      ),
      sessions: analytics.by_session.filter(s =>
        s.session_name.toLowerCase().includes(query) ||
        s.day_label.toLowerCase().includes(query)
      )
    }
  }

  const filteredData = getFilteredData()

  // Sorting function
  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc'
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key, direction })
  }

  // Get sorted data
  const getSortedData = <T extends Record<string, any>>(data: T[], sortKey: string): T[] => {
    if (!sortConfig || sortConfig.key !== sortKey || !data.length) {
      return data
    }

    return [...data].sort((a, b) => {
      let aVal = a[sortKey]
      let bVal = b[sortKey]

      // Handle null/undefined values
      if (aVal == null) aVal = ''
      if (bVal == null) bVal = ''

      // Handle numbers
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal
      }

      // Handle strings
      const aStr = String(aVal).toLowerCase()
      const bStr = String(bVal).toLowerCase()

      if (sortConfig.direction === 'asc') {
        return aStr.localeCompare(bStr)
      } else {
        return bStr.localeCompare(aStr)
      }
    })
  }

  // Get sort icon
  const getSortIcon = (columnKey: string) => {
    if (!sortConfig || sortConfig.key !== columnKey) {
      return <ChevronsUpDown className="w-4 h-4 text-gray-400" />
    }
    return sortConfig.direction === 'asc' 
      ? <ChevronUp className="w-4 h-4 text-purple-600" />
      : <ChevronDown className="w-4 h-4 text-purple-600" />
  }

  // Handle country click
  const handleCountryClick = (countryCode: string) => {
    if (selectedCountry === countryCode) {
      setSelectedCountry(null)
    } else {
      setSelectedCountry(countryCode)
      setSelectedBranch(null) // Clear branch selection when selecting country
    }
  }

  // Handle branch click
  const handleBranchClick = async (branchId: string) => {
    if (selectedBranch === branchId) {
      setSelectedBranch(null)
      setBranchAttendees([])
    } else {
      setSelectedBranch(branchId)
      setSelectedCountry(null) // Clear country selection when selecting branch
      await fetchBranchAttendees(branchId)
    }
  }

  // Fetch attendees for a branch
  const fetchBranchAttendees = async (branchId: string) => {
    if (!selectedConferenceId || !analytics) return

    setLoadingAttendees(true)
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setLoadingAttendees(false)
        return
      }

      // Find branch name from analytics
      const branch = analytics.by_branch.find(b => b.branch_id === branchId)
      if (!branch) {
        setBranchAttendees([])
        setLoadingAttendees(false)
        return
      }

      // Search for registrations in this branch using branch name
      const response = await fetch(
        `${API_BASE_URL}/api/v1/conferences/${selectedConferenceId}/analytics/search?branch=${encodeURIComponent(branch.branch_name)}`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setBranchAttendees(data.registrations || [])
      } else {
        setBranchAttendees([])
      }
    } catch (err) {
      console.error('Failed to fetch branch attendees:', err)
      setBranchAttendees([])
    } finally {
      setLoadingAttendees(false)
    }
  }

  // Get branches for selected country
  const getCountryBranches = () => {
    if (!selectedCountry || !analytics) return []
    
    const country = analytics.by_country.find(c => c.country_code === selectedCountry)
    if (!country) return []

    // Get branch data from analytics
    const branchMap = new Map<string, { name: string; count: number }>()
    
    // Collect branches from all branch analytics that have this country
    analytics.by_branch.forEach(branch => {
      const countryCount = branch.countries[country.country_name] || 0
      if (countryCount > 0) {
        branchMap.set(branch.branch_id, {
          name: branch.branch_name,
          count: countryCount
        })
      }
    })

    // Also use the branches data from country analytics
    Object.entries(country.branches).forEach(([branchName, count]) => {
      // Find branch ID if exists
      const existingBranch = analytics.by_branch.find(b => b.branch_name === branchName)
      if (existingBranch) {
        branchMap.set(existingBranch.branch_id, {
          name: branchName,
          count: Math.max(count, branchMap.get(existingBranch.branch_id)?.count || 0)
        })
      } else {
        // Use a temporary key for branches not in the main list
        branchMap.set(`temp_${branchName}`, {
          name: branchName,
          count
        })
      }
    })

    return Array.from(branchMap.values()).sort((a, b) => b.count - a.count)
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
            Conference Analytics
          </h1>
          <p className="text-gray-600">
            Comprehensive analytics for conference attendees by branch, country, and session
          </p>
        </div>

        {/* Conference Selector (hidden when conferenceId prop is provided) */}
        {!conferenceId && (
          <div className="bg-white rounded-xl shadow-sm border p-4 sm:p-6 mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Conference
            </label>
            <select
              value={selectedConferenceId}
              onChange={(e) => setSelectedConferenceId(e.target.value)}
              className="w-full md:w-auto px-4 py-2 min-h-[44px] text-base border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="">Select a conference...</option>
              {conferences.map(conf => (
                <option key={conf.id} value={conf.id}>
                  {conf.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* AI Summary Section */}
        {analytics && (
          <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-purple-600" />
              <h2 className="text-lg font-semibold text-gray-900">AI-Powered Summary</h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Summary Type
                  </label>
                  <select
                    value={summaryType}
                    onChange={(e) => {
                      setSummaryType(e.target.value)
                      setSummary(null)
                      setSummaryError(null)
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="overview">Overview Summary</option>
                    <option value="branch_analysis">Branch Analysis</option>
                    <option value="country_analysis">Country Analysis</option>
                    <option value="session_attendance">Session Attendance</option>
                    <option value="check_in_performance">Check-in Performance</option>
                    <option value="custom">Custom Analysis</option>
                  </select>
                </div>
                
                <div className="flex items-end">
                  <button
                    onClick={generateSummary}
                    disabled={generatingSummary || (summaryType === 'custom' && !customPrompt.trim())}
                    className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {generatingSummary ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        Generate Summary
                      </>
                    )}
                  </button>
                </div>
              </div>

              {summaryType === 'custom' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Custom Prompt
                  </label>
                  <textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder="Enter your custom analysis request (e.g., 'Analyze the top performing branches and provide recommendations')"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    rows={3}
                  />
                </div>
              )}

              {summaryError && (
                <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
                  {summaryError}
                </div>
              )}

              {summary && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-purple-900">Generated Summary</h3>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={copySummaryToClipboard}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm text-purple-700 hover:text-purple-800 hover:bg-purple-100 rounded-lg transition-colors"
                        title="Copy to clipboard"
                      >
                        {copiedSummary ? (
                          <>
                            <Check className="w-4 h-4" />
                            <span>Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                      <button
                        onClick={() => {
                          setSummary(null)
                          setSummaryError(null)
                        }}
                        className="text-purple-600 hover:text-purple-700"
                        title="Close"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                    {summary}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Search Bar */}
        {analytics && (
          <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 flex gap-2">
                <select
                  value={searchType}
                  onChange={(e) => setSearchType(e.target.value as 'country' | 'branch')}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                >
                  <option value="country">Search by Country</option>
                  <option value="branch">Search by Branch</option>
                </select>
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder={`Search ${searchType}...`}
                    className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  {searchQuery && (
                    <button
                      onClick={clearSearch}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
                <button
                  onClick={handleSearch}
                  disabled={!searchQuery.trim() || searching}
                  className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Search className="w-4 h-4" />
                  Search
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-xl shadow-sm border p-6 text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading analytics...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
            {error}
          </div>
        )}

        {/* Analytics Content */}
        {analytics && !loading && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-gray-600 text-sm font-medium">Total Registrations</p>
                  <Users className="w-5 h-5 text-purple-600" />
                </div>
                <p className="text-3xl font-bold text-gray-900">{analytics.total_registrations}</p>
                <p className="text-sm text-gray-500 mt-1">
                  {analytics.total_checked_in} checked in ({Math.round((analytics.total_checked_in / analytics.total_registrations) * 100) || 0}%)
                </p>
              </div>

              <div className="bg-white rounded-xl shadow-sm border p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-gray-600 text-sm font-medium">Branches</p>
                  <MapPin className="w-5 h-5 text-blue-600" />
                </div>
                <p className="text-3xl font-bold text-gray-900">{analytics.by_branch.length}</p>
                <p className="text-sm text-gray-500 mt-1">Branches represented</p>
              </div>

              <div className="bg-white rounded-xl shadow-sm border p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-gray-600 text-sm font-medium">Countries</p>
                  <BarChart3 className="w-5 h-5 text-green-600" />
                </div>
                <p className="text-3xl font-bold text-gray-900">{analytics.by_country.length}</p>
                <p className="text-sm text-gray-500 mt-1">Countries represented</p>
              </div>
            </div>

            {/* Tabs */}
            <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
              <div className="flex border-b border-gray-200 mb-4 overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
                <button
                  onClick={() => setActiveTab('branch')}
                  className={`px-4 sm:px-6 py-3 min-h-[44px] font-medium text-sm border-b-2 transition-colors whitespace-nowrap touch-manipulation ${
                    activeTab === 'branch'
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  By Branch
                </button>
                <button
                  onClick={() => setActiveTab('country')}
                  className={`px-4 sm:px-6 py-3 min-h-[44px] font-medium text-sm border-b-2 transition-colors whitespace-nowrap touch-manipulation ${
                    activeTab === 'country'
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  By Country
                </button>
                <button
                  onClick={() => setActiveTab('session')}
                  className={`px-4 sm:px-6 py-3 min-h-[44px] font-medium text-sm border-b-2 transition-colors whitespace-nowrap touch-manipulation ${
                    activeTab === 'session'
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  }`}
                >
                  By Session
                </button>
              </div>

              {/* Branch Analytics */}
              {activeTab === 'branch' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Top Branches
                  </h3>
                  <div className="space-y-4">
                    {analytics.top_branches.map((branch, idx) => (
                      <div key={branch.branch_id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm font-medium text-gray-500">#{idx + 1}</span>
                              <h4 className="font-semibold text-gray-900">{branch.branch_name}</h4>
                              <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded">{branch.percentage.toFixed(1)}%</span>
                            </div>
                            {branch.branch_location && (
                              <p className="text-sm text-gray-600">{branch.branch_location}</p>
                            )}
                          </div>
                          <div className="text-right">
                            <p className="text-2xl font-bold text-gray-900">{branch.total_registrations}</p>
                            <p className="text-xs text-gray-500">registrations</p>
                          </div>
                        </div>
                        <div className="mt-3">
                          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                            <div
                              className="bg-purple-600 h-2 rounded-full transition-all"
                              style={{ width: `${branch.percentage}%` }}
                            ></div>
                          </div>
                          <div className="flex justify-between text-xs text-gray-600">
                            <span>{branch.checked_in_count} checked in ({branch.checked_in_percentage.toFixed(1)}%)</span>
                            <span>{branch.total_registrations} total</span>
                          </div>
                        </div>
                        {Object.keys(branch.countries).length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-100">
                            <p className="text-xs font-medium text-gray-500 mb-1">Countries:</p>
                            <div className="flex flex-wrap gap-2">
                              {Object.entries(branch.countries)
                                .sort((a, b) => b[1] - a[1])
                                .slice(0, 5)
                                .map(([country, count]) => (
                                  <span key={country} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                                    {country} ({count})
                                  </span>
                                ))}
                              {Object.keys(branch.countries).length > 5 && (
                                <span className="text-xs text-gray-500">
                                  +{Object.keys(branch.countries).length - 5} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* All Branches Table */}
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">All Branches</h3>

                    {/* Desktop Table View */}
                    <div className="hidden lg:block overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th
                              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('branch_name')}
                            >
                              <div className="flex items-center gap-1">
                                Branch
                                {getSortIcon('branch_name')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('branch_location')}
                            >
                              <div className="flex items-center gap-1">
                                Location
                                {getSortIcon('branch_location')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('total_registrations')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Registrations
                                {getSortIcon('total_registrations')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('percentage')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Percentage
                                {getSortIcon('percentage')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('checked_in_count')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Checked In
                                {getSortIcon('checked_in_count')}
                              </div>
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {getSortedData(filteredData.branches, 'branch_name').map(branch => (
                            <tr
                              key={branch.branch_id}
                              className={`hover:bg-gray-50 cursor-pointer transition-colors ${selectedBranch === branch.branch_id ? 'bg-purple-50' : ''}`}
                              onClick={() => handleBranchClick(branch.branch_id)}
                            >
                              <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                <div className="flex items-center gap-2">
                                  {branch.branch_name}
                                  {selectedBranch === branch.branch_id && (
                                    <ChevronDown className="w-4 h-4 text-purple-600" />
                                  )}
                                </div>
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-600">{branch.branch_location || 'N/A'}</td>
                              <td className="px-4 py-3 text-sm text-right text-gray-900">{branch.total_registrations}</td>
                              <td className="px-4 py-3 text-sm text-right text-gray-600">{branch.percentage.toFixed(2)}%</td>
                              <td className="px-4 py-3 text-sm text-right text-gray-600">
                                {branch.checked_in_count} ({branch.checked_in_percentage.toFixed(1)}%)
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Mobile Card View */}
                    <div className="lg:hidden space-y-3">
                      {getSortedData(filteredData.branches, 'branch_name').map(branch => (
                        <div
                          key={branch.branch_id}
                          className={`bg-white border-2 rounded-lg p-4 cursor-pointer transition-all touch-manipulation ${
                            selectedBranch === branch.branch_id ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-gray-300'
                          }`}
                          onClick={() => handleBranchClick(branch.branch_id)}
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className="text-sm font-semibold text-gray-900 truncate">{branch.branch_name}</h4>
                                {selectedBranch === branch.branch_id && (
                                  <ChevronDown className="w-4 h-4 text-purple-600 flex-shrink-0" />
                                )}
                              </div>
                              {branch.branch_location && (
                                <p className="text-xs text-gray-500 flex items-center gap-1">
                                  <MapPin className="w-3 h-3" />
                                  {branch.branch_location}
                                </p>
                              )}
                            </div>
                            <div className="text-right ml-3">
                              <div className="text-lg font-bold text-gray-900">{branch.total_registrations}</div>
                              <div className="text-xs text-gray-500">registrations</div>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-200">
                            <div>
                              <div className="text-xs text-gray-500 mb-0.5">Percentage</div>
                              <div className="text-sm font-medium text-gray-900">{branch.percentage.toFixed(2)}%</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500 mb-0.5">Checked In</div>
                              <div className="text-sm font-medium text-gray-900">
                                {branch.checked_in_count} ({branch.checked_in_percentage.toFixed(1)}%)
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Branch Attendees Detail View */}
                    {selectedBranch && (
                      <div className="mt-4 bg-purple-50 border border-purple-200 rounded-lg p-6">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-lg font-semibold text-gray-900">
                            Attendees in {analytics?.by_branch.find(b => b.branch_id === selectedBranch)?.branch_name}
                          </h4>
                          <button
                            onClick={() => {
                              setSelectedBranch(null)
                              setBranchAttendees([])
                            }}
                            className="text-gray-500 hover:text-gray-700"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </div>
                        {loadingAttendees ? (
                          <div className="text-center py-8">
                            <Loader2 className="w-6 h-6 animate-spin text-purple-600 mx-auto mb-2" />
                            <p className="text-sm text-gray-600">Loading attendees...</p>
                          </div>
                        ) : branchAttendees.length > 0 ? (
                          <>
                            {/* Desktop Table View */}
                            <div className="hidden md:block overflow-x-auto">
                              <table className="w-full">
                                <thead className="bg-white">
                                  <tr>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Country</th>
                                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                  </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                  {branchAttendees.map((attendee) => (
                                    <tr key={attendee.id} className="hover:bg-gray-50">
                                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{attendee.user_name || 'N/A'}</td>
                                      <td className="px-4 py-3 text-sm text-gray-600">{attendee.user_phone || 'N/A'}</td>
                                      <td className="px-4 py-3 text-sm text-gray-600">{attendee.user_email || 'N/A'}</td>
                                      <td className="px-4 py-3 text-sm text-gray-600">{attendee.country_name || 'N/A'}</td>
                                      <td className="px-4 py-3 text-sm">
                                        <span className={`px-2 py-1 rounded text-xs ${
                                          attendee.checked_in ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                                        }`}>
                                          {attendee.checked_in ? 'Checked In' : 'Not Checked In'}
                                        </span>
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>

                            {/* Mobile Card View */}
                            <div className="md:hidden space-y-3">
                              {branchAttendees.map((attendee) => (
                                <div key={attendee.id} className="bg-white border border-gray-200 rounded-lg p-3">
                                  <div className="flex items-start justify-between mb-2">
                                    <div className="font-medium text-sm text-gray-900">{attendee.user_name || 'N/A'}</div>
                                    <span className={`px-2 py-0.5 rounded text-xs flex-shrink-0 ml-2 ${
                                      attendee.checked_in ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                                    }`}>
                                      {attendee.checked_in ? 'Checked In' : 'Not Checked In'}
                                    </span>
                                  </div>
                                  <div className="space-y-1 text-xs text-gray-600">
                                    <div><span className="text-gray-500">Phone:</span> {attendee.user_phone || 'N/A'}</div>
                                    {attendee.user_email && <div className="truncate"><span className="text-gray-500">Email:</span> {attendee.user_email}</div>}
                                    <div><span className="text-gray-500">Country:</span> {attendee.country_name || 'N/A'}</div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </>
                        ) : (
                          <p className="text-gray-500 text-sm">No attendees found for this branch.</p>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Country Analytics */}
              {activeTab === 'country' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Top Countries
                  </h3>
                  <div className="space-y-4">
                    {analytics.top_countries.map((country, idx) => (
                      <div key={country.country_code} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm font-medium text-gray-500">#{idx + 1}</span>
                              <h4 className="font-semibold text-gray-900">{country.country_name}</h4>
                              <span className="text-xs text-gray-500">({country.country_code})</span>
                              <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded">{country.percentage.toFixed(1)}%</span>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-2xl font-bold text-gray-900">{country.total_registrations}</p>
                            <p className="text-xs text-gray-500">registrations</p>
                          </div>
                        </div>
                        <div className="mt-3">
                          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                            <div
                              className="bg-green-600 h-2 rounded-full transition-all"
                              style={{ width: `${country.percentage}%` }}
                            ></div>
                          </div>
                          <div className="flex justify-between text-xs text-gray-600">
                            <span>{country.checked_in_count} checked in ({country.checked_in_percentage.toFixed(1)}%)</span>
                            <span>{country.total_registrations} total</span>
                          </div>
                        </div>
                        {Object.keys(country.branches).length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-100">
                            <p className="text-xs font-medium text-gray-500 mb-1">Branches:</p>
                            <div className="flex flex-wrap gap-2">
                              {Object.entries(country.branches)
                                .sort((a, b) => b[1] - a[1])
                                .slice(0, 5)
                                .map(([branch, count]) => (
                                  <span key={branch} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                                    {branch} ({count})
                                  </span>
                                ))}
                              {Object.keys(country.branches).length > 5 && (
                                <span className="text-xs text-gray-500">
                                  +{Object.keys(country.branches).length - 5} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {/* All Countries Table */}
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">All Countries</h3>

                    {/* Desktop Table View */}
                    <div className="hidden lg:block overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th
                              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('country_name')}
                            >
                              <div className="flex items-center gap-1">
                                Country
                                {getSortIcon('country_name')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('country_code')}
                            >
                              <div className="flex items-center gap-1">
                                Code
                                {getSortIcon('country_code')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('total_registrations')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Registrations
                                {getSortIcon('total_registrations')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('percentage')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Percentage
                                {getSortIcon('percentage')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('checked_in_count')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Checked In
                                {getSortIcon('checked_in_count')}
                              </div>
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {getSortedData(filteredData.countries, 'country_name').map(country => (
                            <tr
                              key={country.country_code}
                              className={`hover:bg-gray-50 cursor-pointer transition-colors ${selectedCountry === country.country_code ? 'bg-purple-50' : ''}`}
                              onClick={() => handleCountryClick(country.country_code)}
                            >
                              <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                <div className="flex items-center gap-2">
                                  {country.country_name}
                                  {selectedCountry === country.country_code && (
                                    <ChevronDown className="w-4 h-4 text-purple-600" />
                                  )}
                                </div>
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-600">{country.country_code}</td>
                              <td className="px-4 py-3 text-sm text-right text-gray-900">{country.total_registrations}</td>
                              <td className="px-4 py-3 text-sm text-right text-gray-600">{country.percentage.toFixed(2)}%</td>
                              <td className="px-4 py-3 text-sm text-right text-gray-600">
                                {country.checked_in_count} ({country.checked_in_percentage.toFixed(1)}%)
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Mobile Card View */}
                    <div className="lg:hidden space-y-3">
                      {getSortedData(filteredData.countries, 'country_name').map(country => (
                        <div
                          key={country.country_code}
                          className={`bg-white border-2 rounded-lg p-4 cursor-pointer transition-all touch-manipulation ${
                            selectedCountry === country.country_code ? 'border-purple-500 bg-purple-50' : 'border-gray-200 hover:border-gray-300'
                          }`}
                          onClick={() => handleCountryClick(country.country_code)}
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className="text-sm font-semibold text-gray-900 truncate">{country.country_name}</h4>
                                {selectedCountry === country.country_code && (
                                  <ChevronDown className="w-4 h-4 text-purple-600 flex-shrink-0" />
                                )}
                              </div>
                              <p className="text-xs text-gray-500">Code: {country.country_code}</p>
                            </div>
                            <div className="text-right ml-3">
                              <div className="text-lg font-bold text-gray-900">{country.total_registrations}</div>
                              <div className="text-xs text-gray-500">registrations</div>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-200">
                            <div>
                              <div className="text-xs text-gray-500 mb-0.5">Percentage</div>
                              <div className="text-sm font-medium text-gray-900">{country.percentage.toFixed(2)}%</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500 mb-0.5">Checked In</div>
                              <div className="text-sm font-medium text-gray-900">
                                {country.checked_in_count} ({country.checked_in_percentage.toFixed(1)}%)
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Country Branches Modal/Expansion */}
                    {selectedCountry && (
                      <div className="mt-4 bg-purple-50 border border-purple-200 rounded-lg p-6">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-lg font-semibold text-gray-900">
                            Branches in {analytics?.by_country.find(c => c.country_code === selectedCountry)?.country_name}
                          </h4>
                          <button
                            onClick={() => setSelectedCountry(null)}
                            className="text-gray-500 hover:text-gray-700"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </div>
                        <div className="space-y-2">
                          {getCountryBranches().length > 0 ? (
                            getCountryBranches().map((branch, idx) => (
                              <div key={idx} className="bg-white rounded-lg p-4 border border-purple-100">
                                <div className="flex items-center justify-between">
                                  <span className="font-medium text-gray-900">{branch.name}</span>
                                  <span className="text-sm text-gray-600">{branch.count} registrations</span>
                                </div>
                              </div>
                            ))
                          ) : (
                            <p className="text-gray-500 text-sm">No branch data available for this country.</p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Session Analytics */}
              {activeTab === 'session' && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Top Sessions
                  </h3>
                  <div className="space-y-4">
                    {analytics.top_sessions.map((session, idx) => (
                      <div key={session.session_id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm font-medium text-gray-500">#{idx + 1}</span>
                              <h4 className="font-semibold text-gray-900">{session.session_name}</h4>
                              <span className="text-xs text-gray-500">({session.day_label})</span>
                              <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">{session.percentage.toFixed(1)}%</span>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-2xl font-bold text-gray-900">{session.total_checked_in}</p>
                            <p className="text-xs text-gray-500">checked in</p>
                          </div>
                        </div>
                        <div className="mt-3">
                          <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${session.percentage}%` }}
                            ></div>
                          </div>
                          <div className="flex justify-between text-xs text-gray-600">
                            <span>{session.unique_attendees} unique attendees</span>
                            <span>{session.total_checked_in} check-ins</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* All Sessions Table */}
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">All Sessions</h3>

                    {/* Desktop Table View */}
                    <div className="hidden lg:block overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gray-50">
                          <tr>
                            <th
                              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('session_name')}
                            >
                              <div className="flex items-center gap-1">
                                Session
                                {getSortIcon('session_name')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('day_number')}
                            >
                              <div className="flex items-center gap-1">
                                Day
                                {getSortIcon('day_number')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('total_checked_in')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Checked In
                                {getSortIcon('total_checked_in')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('percentage')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Percentage
                                {getSortIcon('percentage')}
                              </div>
                            </th>
                            <th
                              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:bg-gray-100"
                              onClick={() => handleSort('unique_attendees')}
                            >
                              <div className="flex items-center justify-end gap-1">
                                Unique Attendees
                                {getSortIcon('unique_attendees')}
                              </div>
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {getSortedData(filteredData.sessions, 'session_name').map(session => (
                            <tr key={session.session_id} className="hover:bg-gray-50">
                              <td className="px-4 py-3 text-sm font-medium text-gray-900">{session.session_name}</td>
                              <td className="px-4 py-3 text-sm text-gray-600">{session.day_label}</td>
                              <td className="px-4 py-3 text-sm text-right text-gray-900">{session.total_checked_in}</td>
                              <td className="px-4 py-3 text-sm text-right text-gray-600">{session.percentage.toFixed(2)}%</td>
                              <td className="px-4 py-3 text-sm text-right text-gray-600">{session.unique_attendees}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Mobile Card View */}
                    <div className="lg:hidden space-y-3">
                      {getSortedData(filteredData.sessions, 'session_name').map(session => (
                        <div key={session.session_id} className="bg-white border-2 border-gray-200 rounded-lg p-4">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1 min-w-0">
                              <h4 className="text-sm font-semibold text-gray-900 mb-1">{session.session_name}</h4>
                              <p className="text-xs text-gray-500 flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {session.day_label}
                              </p>
                            </div>
                            <div className="text-right ml-3">
                              <div className="text-lg font-bold text-gray-900">{session.total_checked_in}</div>
                              <div className="text-xs text-gray-500">checked in</div>
                            </div>
                          </div>
                          <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-200">
                            <div>
                              <div className="text-xs text-gray-500 mb-0.5">Percentage</div>
                              <div className="text-sm font-medium text-gray-900">{session.percentage.toFixed(2)}%</div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500 mb-0.5">Unique Attendees</div>
                              <div className="text-sm font-medium text-gray-900">{session.unique_attendees}</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border p-6 mt-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Search Results ({searchResults.length})
                  </h3>
                  <button
                    onClick={clearSearch}
                    className="text-sm text-purple-600 hover:text-purple-700"
                  >
                    Clear
                  </button>
                </div>
                {/* Desktop Table View */}
                <div className="hidden md:block overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Country</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Branch</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {searchResults.map(reg => (
                        <tr key={reg.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">{reg.user_name}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{reg.user_phone}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{reg.country_name}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{reg.branch_name || reg.church_name || 'N/A'}</td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`px-2 py-1 rounded text-xs ${
                              reg.checked_in ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {reg.checked_in ? 'Checked In' : 'Not Checked In'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Mobile Card View */}
                <div className="md:hidden space-y-3">
                  {searchResults.map(reg => (
                    <div key={reg.id} className="bg-white border border-gray-200 rounded-lg p-3">
                      <div className="flex items-start justify-between mb-2">
                        <div className="font-medium text-sm text-gray-900">{reg.user_name}</div>
                        <span className={`px-2 py-0.5 rounded text-xs flex-shrink-0 ml-2 ${
                          reg.checked_in ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {reg.checked_in ? 'Checked In' : 'Not Checked In'}
                        </span>
                      </div>
                      <div className="space-y-1 text-xs text-gray-600">
                        <div><span className="text-gray-500">Phone:</span> {reg.user_phone}</div>
                        <div><span className="text-gray-500">Country:</span> {reg.country_name}</div>
                        <div><span className="text-gray-500">Branch:</span> {reg.branch_name || reg.church_name || 'N/A'}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Empty State */}
        {!loading && !error && !analytics && selectedConferenceId && (
          <div className="bg-white rounded-xl shadow-sm border p-6 text-center py-12">
            <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No analytics data available for this conference.</p>
          </div>
        )}
      </div>
    </div>
  )
}

