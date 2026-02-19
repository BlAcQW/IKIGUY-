/**
 * Visitor List Page
 *
 * Displays recent visitors with infinite scroll, filtering, search, and quick actions.
 * Allows viewing visitor details and assigning to cell groups.
 *
 * URL: /visitors
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  UserPlus,
  Search,
  Filter,
  Users,
  Calendar,
  Phone,
  Mail,
  Loader,
  AlertCircle,
  RefreshCw,
  Send,
  TrendingUp,
  UserCheck,
  BarChart3,
  Trash2,
  X,
  Edit,
  Eye,
} from 'lucide-react';
import { visitorApi, type Visitor, type VisitorStats } from '../services/visitorApi';
import { formatDistanceToNow } from 'date-fns';
import StatCard from '../components/visitor-stats/StatCard';
import StatCardSkeleton from '../components/visitor-stats/StatCardSkeleton';
import { useInfiniteScroll } from '../hooks/useInfiniteScroll';

const PAGE_SIZE = 50;

export default function VisitorList() {
  const navigate = useNavigate();
  const [visitors, setVisitors] = useState<Visitor[]>([]);
  const [overallStats, setOverallStats] = useState<VisitorStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [daysFilter, setDaysFilter] = useState<number>(7);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);

  // Selection state for bulk operations
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Load stats
  useEffect(() => {
    loadStats();
  }, []);

  // Reset and reload when filters change
  useEffect(() => {
    setVisitors([]);
    setCurrentPage(1);
    setHasMore(true);
    loadVisitors(1, false);
  }, [daysFilter]);

  const loadVisitors = useCallback(async (page: number, append: boolean = false) => {
    if (append) {
      setIsLoadingMore(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const response = await visitorApi.getRecentVisitors({
        days: daysFilter,
        limit: PAGE_SIZE,
        skip: (page - 1) * PAGE_SIZE,
      });

      const newVisitors = response.visitors || [];
      const totalCount = response.total || 0;

      if (append) {
        setVisitors(prev => [...prev, ...newVisitors]);
      } else {
        setVisitors(newVisitors);
      }

      setTotal(totalCount);
      setHasMore(page * PAGE_SIZE < totalCount);
    } catch (err: any) {
      console.error('Failed to load visitors:', err);
      setError(err.response?.data?.detail || 'Failed to load visitors');
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, [daysFilter]);

  const loadStats = async () => {
    try {
      const stats = await visitorApi.getStats();
      setOverallStats(stats);
    } catch (err: any) {
      console.error('Failed to load stats:', err);
    }
  };

  // Load more handler
  const handleLoadMore = useCallback(() => {
    if (!isLoadingMore && hasMore) {
      const nextPage = currentPage + 1;
      setCurrentPage(nextPage);
      loadVisitors(nextPage, true);
    }
  }, [currentPage, loadVisitors, hasMore, isLoadingMore]);

  // Infinite scroll hook
  const { sentinelRef } = useInfiniteScroll({
    onLoadMore: handleLoadMore,
    hasMore,
    isLoading: isLoading || isLoadingMore,
  });

  // Filter visitors based on search and status (client-side filtering on loaded data)
  const filteredVisitors = useMemo(() => {
    let filtered = visitors;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (visitor) =>
          visitor.name?.toLowerCase().includes(query) ||
          visitor.phone?.includes(query) ||
          visitor.email?.toLowerCase().includes(query)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((visitor) => visitor.member_status === statusFilter);
    }

    return filtered;
  }, [visitors, searchQuery, statusFilter]);

  const handleResendWelcome = async (visitorId: string) => {
    try {
      await visitorApi.resendWelcome(visitorId);
      alert('Welcome message sent successfully!');
    } catch (err: any) {
      console.error('Failed to resend welcome:', err);
      alert(err.response?.data?.detail || 'Failed to send welcome message');
    }
  };

  // Selection handlers
  const handleSelectAll = useCallback((checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(filteredVisitors.map(v => v.id)));
    } else {
      setSelectedIds(new Set());
    }
  }, [filteredVisitors]);

  const handleSelectOne = useCallback((id: string, checked: boolean) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (checked) {
        newSet.add(id);
      } else {
        newSet.delete(id);
      }
      return newSet;
    });
  }, []);

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;

    setIsDeleting(true);
    try {
      const result = await visitorApi.bulkDeleteVisitors(Array.from(selectedIds));
      alert(`Successfully deleted ${result.deleted_count} visitors`);
      setSelectedIds(new Set());
      setShowDeleteModal(false);
      // Refresh the list
      handleRefresh();
    } catch (err: any) {
      console.error('Failed to delete visitors:', err);
      alert(err.response?.data?.detail || 'Failed to delete visitors');
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return dateString;
    }
  };

  // Use overall stats for summary cards (total counts, not filtered)
  const totalUsers = overallStats?.total_users || 0;
  const activeMembers = overallStats?.active_members || 0;
  const totalVisitors = overallStats?.visitors || 0;

  // Calculate filtered stats for trend data (visitors from the selected period)
  const filteredVisitorCount = filteredVisitors.filter(v => v.member_status === 'visitor').length;
  const firstTimers = filteredVisitors.filter(v => v.visit_count === 1).length;
  const returningVisitors = filteredVisitors.filter(v => v.visit_count && v.visit_count > 1).length;
  const avgVisits = filteredVisitors.length > 0
    ? (filteredVisitors.reduce((sum, v) => sum + (v.visit_count || 0), 0) / filteredVisitors.length)
    : 0;

  // Calculate trend data for sparklines (last 7 days) - memoized helper
  const calculateDailyTrend = useCallback((visitorList: Visitor[], days: number = 7) => {
    const dailyCounts = Array(days).fill(0);
    visitorList.forEach(visitor => {
      if (!visitor.created_at) return;
      const daysSinceCreation = Math.floor(
        (Date.now() - new Date(visitor.created_at).getTime()) / (1000 * 60 * 60 * 24)
      );
      if (daysSinceCreation >= 0 && daysSinceCreation < days) {
        dailyCounts[days - 1 - daysSinceCreation]++;
      }
    });
    return dailyCounts;
  }, []);

  // Calculate previous period statistics - now properly memoized
  const previousStats = useMemo(() => {
    const now = new Date();
    const periodStart = new Date();
    periodStart.setDate(now.getDate() - daysFilter);
    const previousPeriodStart = new Date();
    previousPeriodStart.setDate(periodStart.getDate() - daysFilter);

    const previousPeriodVisitors = visitors.filter(v => {
      if (!v.created_at) return false;
      const date = new Date(v.created_at);
      return date >= previousPeriodStart && date < periodStart;
    });

    return {
      totalVisitors: previousPeriodVisitors.filter(v => v.member_status === 'visitor').length,
      firstTimers: previousPeriodVisitors.filter(v => v.visit_count === 1).length,
      returningVisitors: previousPeriodVisitors.filter(v => v.visit_count && v.visit_count > 1).length,
      avgVisits: previousPeriodVisitors.length > 0
        ? (previousPeriodVisitors.reduce((sum, v) => sum + (v.visit_count || 0), 0) / previousPeriodVisitors.length)
        : 0,
    };
  }, [visitors, daysFilter]);

  // Pre-compute trend data once to avoid recalculating in statsCards
  const trendData = useMemo(() => ({
    all: calculateDailyTrend(filteredVisitors),
    activeMembers: calculateDailyTrend(filteredVisitors.filter(v => v.member_status === 'active_member')),
    visitors: calculateDailyTrend(filteredVisitors.filter(v => v.member_status === 'visitor')),
    firstTimers: calculateDailyTrend(filteredVisitors.filter(v => v.visit_count === 1)),
    returning: calculateDailyTrend(filteredVisitors.filter(v => v.visit_count && v.visit_count > 1)),
  }), [filteredVisitors, calculateDailyTrend]);

  // Prepare card data
  const statsCards = useMemo(() => [
    {
      title: 'Total Users',
      value: totalUsers,
      previousValue: undefined,
      icon: Users,
      color: 'purple' as const,
      subtitle: 'All time',
      trendData: trendData.all,
      additionalInfo: 'Total users in the system',
    },
    {
      title: 'Active Members',
      value: activeMembers,
      previousValue: undefined,
      icon: UserCheck,
      color: 'green' as const,
      subtitle: 'With branch assignments',
      trendData: trendData.activeMembers,
      additionalInfo: 'Action Chapel members',
    },
    {
      title: 'Visitors',
      value: totalVisitors,
      previousValue: previousStats.totalVisitors,
      icon: Users,
      color: 'blue' as const,
      subtitle: `Last ${daysFilter}d: ${filteredVisitorCount}`,
      trendData: trendData.visitors,
      additionalInfo: 'From other churches',
    },
    {
      title: 'First Timers',
      value: firstTimers,
      previousValue: previousStats.firstTimers,
      icon: UserPlus,
      color: 'blue' as const,
      subtitle: 'New faces',
      trendData: trendData.firstTimers,
      additionalInfo: 'Visitors attending for the first time',
    },
    {
      title: 'Returning',
      value: returningVisitors,
      previousValue: previousStats.returningVisitors,
      icon: UserCheck,
      color: 'green' as const,
      subtitle: '2+ visits',
      trendData: trendData.returning,
      additionalInfo: 'Visitors who came back after first visit',
    },
    {
      title: 'Avg Visits',
      value: avgVisits,
      previousValue: previousStats.avgVisits,
      icon: BarChart3,
      color: 'orange' as const,
      subtitle: 'Per visitor',
      trendData: trendData.all,
      additionalInfo: 'Average number of visits per visitor',
      decimals: 1,
    },
  ], [totalUsers, activeMembers, totalVisitors, firstTimers, returningVisitors, avgVisits, previousStats, daysFilter, filteredVisitorCount, trendData]);

  const handleRefresh = () => {
    setVisitors([]);
    setCurrentPage(1);
    setHasMore(true);
    loadVisitors(1, false);
    loadStats();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg">
                  <Users className="w-7 h-7 text-white" />
                </div>
                Visitors
              </h1>
              <p className="text-sm text-gray-600 mt-2 flex items-center gap-2">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  {visitors.length} of {total} loaded
                </span>
                <span className="text-gray-400">•</span>
                <span>Last {daysFilter} days</span>
              </p>
            </div>
            <button
              onClick={() => navigate('/visitors/capture')}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-xl hover:from-purple-700 hover:to-purple-800 transition-all duration-300 font-semibold shadow-lg hover:shadow-xl hover:-translate-y-0.5"
            >
              <UserPlus className="w-5 h-5" />
              Capture Visitor
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          <motion.div
            className="contents"
            initial="hidden"
            animate="visible"
            variants={{
              visible: {
                transition: {
                  staggerChildren: 0.1,
                },
              },
            }}
          >
            {isLoading && visitors.length === 0 ? (
              Array(4).fill(0).map((_, i) => (
                <motion.div
                  key={i}
                  variants={{
                    hidden: { opacity: 0, y: 20 },
                    visible: { opacity: 1, y: 0 },
                  }}
                >
                  <StatCardSkeleton />
                </motion.div>
              ))
            ) : (
              statsCards.map((card, i) => (
                <motion.div
                  key={i}
                  variants={{
                    hidden: { opacity: 0, y: 20 },
                    visible: { opacity: 1, y: 0 },
                  }}
                >
                  <StatCard {...card} />
                </motion.div>
              ))
            )}
          </motion.div>
        </div>

        {/* Filters Bar */}
        <div className="bg-white rounded-xl shadow-md border border-gray-200 p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Filter className="w-5 h-5 text-purple-600" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by name, phone, email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 hover:bg-white"
              />
            </div>

            {/* Days Filter */}
            <select
              value={daysFilter}
              onChange={(e) => setDaysFilter(Number(e.target.value))}
              className="px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 hover:bg-white font-medium"
            >
              <option value={7}>Last 7 days</option>
              <option value={14}>Last 14 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
              <option value={365}>Last year</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-200 bg-gray-50 hover:bg-white font-medium"
            >
              <option value="all">All Statuses</option>
              <option value="visitor">Visitors Only</option>
              <option value="active_member">Active Members</option>
              <option value="inactive_member">Inactive</option>
              <option value="alumni">Alumni</option>
            </select>
          </div>

          <div className="mt-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={handleRefresh}
                disabled={isLoading}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-all duration-200 disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              {selectedIds.size > 0 && (
                <button
                  onClick={() => setShowDeleteModal(true)}
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-all duration-200"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete ({selectedIds.size})
                </button>
              )}
            </div>
            <p className="text-sm text-gray-500">
              {selectedIds.size > 0 ? (
                <span className="text-purple-600 font-medium">{selectedIds.size} selected</span>
              ) : (
                `Showing ${filteredVisitors.length} of ${total} total`
              )}
            </p>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 bg-gradient-to-r from-red-50 to-red-100 border-2 border-red-200 rounded-xl p-6 shadow-md">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-red-200 rounded-lg">
                <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-red-900 text-lg">Error Loading Visitors</h3>
                <p className="text-sm text-red-700 mt-2">{error}</p>
                <button
                  onClick={handleRefresh}
                  className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all duration-200 font-semibold"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Initial Loading State */}
        {isLoading && visitors.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 bg-white rounded-xl shadow-md">
            <div className="relative">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-purple-700 rounded-full animate-pulse"></div>
              <Loader className="w-10 h-10 text-white animate-spin absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
            </div>
            <p className="text-gray-700 font-medium mt-6">Loading visitors...</p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && filteredVisitors.length === 0 && visitors.length === 0 && (
          <div className="bg-gradient-to-br from-white to-purple-50 rounded-xl shadow-md border-2 border-purple-100 p-16 text-center">
            <div className="p-4 bg-purple-100 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
              <Users className="w-10 h-10 text-purple-600" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">No Visitors Found</h3>
            <p className="text-gray-600 mb-8 text-lg">
              {searchQuery
                ? 'Try adjusting your search or filters'
                : `No visitors in the last ${daysFilter} days`}
            </p>
            <button
              onClick={() => navigate('/visitors/capture')}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-xl hover:from-purple-700 hover:to-purple-800 transition-all duration-300 font-semibold shadow-lg hover:shadow-xl hover:-translate-y-0.5"
            >
              <UserPlus className="w-5 h-5" />
              Capture First Visitor
            </button>
          </div>
        )}

        {/* Visitors List */}
        {(visitors.length > 0 || (filteredVisitors.length > 0)) && (
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gradient-to-r from-purple-50 to-blue-50 border-b-2 border-purple-200 sticky top-0">
                  <tr>
                    <th className="px-4 py-4 text-left">
                      <input
                        type="checkbox"
                        checked={filteredVisitors.length > 0 && selectedIds.size === filteredVisitors.length}
                        onChange={(e) => handleSelectAll(e.target.checked)}
                        className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                      />
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">
                      Visits
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">
                      First Visit
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">
                      Spiritual Stage
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-purple-900 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredVisitors.map((visitor) => (
                    <tr
                      key={visitor.id}
                      className={`hover:bg-gradient-to-r hover:from-purple-50 hover:to-blue-50 transition-all duration-200 cursor-pointer group ${
                        selectedIds.has(visitor.id) ? 'bg-purple-50' : ''
                      }`}
                    >
                      <td className="px-4 py-4 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={selectedIds.has(visitor.id)}
                          onChange={(e) => handleSelectOne(visitor.id, e.target.checked)}
                          className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                        />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap" onClick={() => navigate(`/visitors/${visitor.id}`)}>
                        <div className="font-medium text-gray-900 group-hover:text-purple-700 transition-colors">
                          {visitor.name || visitor.full_name || 'Unnamed Visitor'}
                        </div>
                      </td>
                      <td className="px-6 py-4" onClick={() => navigate(`/visitors/${visitor.id}`)}>
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Phone className="w-4 h-4 flex-shrink-0" />
                            <span>{visitor.phone}</span>
                          </div>
                          {visitor.email && (
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <Mail className="w-4 h-4 flex-shrink-0" />
                              <span className="truncate max-w-xs">{visitor.email}</span>
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap" onClick={() => navigate(`/visitors/${visitor.id}`)}>
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-600 rounded-full flex items-center justify-center">
                            <span className="text-white font-bold text-sm">{visitor.visit_count}</span>
                          </div>
                          <span className="text-xs text-gray-500 font-medium">visits</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap" onClick={() => navigate(`/visitors/${visitor.id}`)}>
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-700 font-medium">{formatDate(visitor.first_visit_date)}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap" onClick={() => navigate(`/visitors/${visitor.id}`)}>
                        {visitor.current_spiritual_stage && (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 capitalize">
                            {visitor.current_spiritual_stage.replace(/_/g, ' ')}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/visitors/${visitor.id}`);
                            }}
                            className="inline-flex items-center gap-1 px-2 py-2 text-gray-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-all duration-200"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/visitors/${visitor.id}/edit`);
                            }}
                            className="inline-flex items-center gap-1 px-2 py-2 text-gray-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-all duration-200"
                            title="Edit Visitor"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleResendWelcome(visitor.id);
                            }}
                            className="inline-flex items-center gap-1 px-2 py-2 text-gray-600 hover:text-green-700 hover:bg-green-50 rounded-lg transition-all duration-200"
                            title="Send Welcome Message"
                          >
                            <Send className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Infinite scroll sentinel and loading indicator */}
            <div ref={sentinelRef} className="py-4">
              {isLoadingMore && (
                <div className="flex items-center justify-center gap-2 text-gray-500">
                  <Loader className="h-5 w-5 animate-spin" />
                  <span>Loading more visitors...</span>
                </div>
              )}
              {!hasMore && visitors.length > 0 && (
                <p className="text-center text-gray-500 text-sm">
                  All {total} visitors loaded
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full">
            <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4 flex items-center justify-between rounded-t-2xl">
              <div className="flex items-center gap-3">
                <Trash2 className="w-6 h-6 text-white" />
                <h2 className="text-xl font-semibold text-white">Delete Visitors</h2>
              </div>
              <button
                onClick={() => setShowDeleteModal(false)}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-white" />
              </button>
            </div>

            <div className="p-6">
              <p className="text-gray-700 mb-4">
                Are you sure you want to delete <span className="font-bold text-red-600">{selectedIds.size}</span> selected visitor{selectedIds.size > 1 ? 's' : ''}?
              </p>
              <p className="text-sm text-gray-500 mb-6">
                This action cannot be undone. All data associated with these visitors will be permanently removed.
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  disabled={isDeleting}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleBulkDelete}
                  disabled={isDeleting}
                  className="flex-1 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isDeleting ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      <span>Deleting...</span>
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-5 h-5" />
                      <span>Delete</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
