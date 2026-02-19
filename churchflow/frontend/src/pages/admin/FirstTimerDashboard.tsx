import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Users, TrendingUp, Calendar, UserCheck, UserPlus, AlertCircle, Filter, Edit, UserCog, Loader, Trash2, X, Eye } from 'lucide-react';
import { API_ENDPOINTS } from '../../config/api-config';
import FirstTimerFormModal from '../../components/first-timers/FirstTimerFormModal';
import ConvertToMemberModal from '../../components/first-timers/ConvertToMemberModal';
import { useInfiniteScroll } from '../../hooks/useInfiniteScroll';
import axios from '../../lib/axios-config';

const PAGE_SIZE = 20;

// Types
interface FirstTimer {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone: string;
  email?: string;
  visit_date: string;
  interest_type: 'visitor' | 'new_convert' | 'existing_member' | 'discipleship';
  wants_membership: boolean;
  wants_discipleship: boolean;
  follow_up_status: 'pending' | 'contacted' | 'in_progress' | 'converted' | 'lost';
  converted_to_member: boolean;
  member_id?: string;
  created_at: string;
}

interface FirstTimerStats {
  total_first_timers: number;
  today: number;
  this_week: number;
  this_month: number;
  visitors: number;
  new_converts: number;
  existing_members: number;
  discipleship_interested: number;
  pending_follow_up: number;
  contacted: number;
  in_progress: number;
  converted: number;
  lost: number;
  conversion_rate: number;
}

const FirstTimerDashboard: React.FC = () => {
  const [stats, setStats] = useState<FirstTimerStats | null>(null);
  const [firstTimers, setFirstTimers] = useState<FirstTimer[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filterInterestType, setFilterInterestType] = useState<string>('');
  const [filterFollowUpStatus, setFilterFollowUpStatus] = useState<string>('');
  const [filterConverted, setFilterConverted] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showConvertModal, setShowConvertModal] = useState(false);
  const [selectedFirstTimer, setSelectedFirstTimer] = useState<FirstTimer | null>(null);

  // Selection state for bulk operations
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  // Reset and reload when filters change
  useEffect(() => {
    setFirstTimers([]);
    setCurrentPage(1);
    setHasMore(true);
    fetchFirstTimers(1, false);
  }, [filterInterestType, filterFollowUpStatus, filterConverted]);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.FIRST_TIMERS.STATS, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch statistics' }));
        console.error('API Error Response:', errorData);
        throw new Error(errorData.detail || 'Failed to fetch statistics');
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Error fetching stats:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const fetchFirstTimers = useCallback(async (page: number, append: boolean = false) => {
    try {
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }

      const token = localStorage.getItem('access_token');
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: PAGE_SIZE.toString(),
      });

      if (filterInterestType) params.append('interest_type', filterInterestType);
      if (filterFollowUpStatus) params.append('follow_up_status', filterFollowUpStatus);
      if (filterConverted) params.append('converted_to_member', filterConverted);

      const response = await fetch(`${API_ENDPOINTS.FIRST_TIMERS.BASE}?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch first timers' }));
        console.error('API Error Response:', errorData);
        throw new Error(errorData.detail || 'Failed to fetch first timers');
      }

      const data = await response.json();
      const newItems = data.items || [];
      const totalCount = data.total || 0;
      const totalPagesCount = data.total_pages || 1;

      if (append) {
        setFirstTimers(prev => [...prev, ...newItems]);
      } else {
        setFirstTimers(newItems);
      }

      setTotal(totalCount);
      setTotalPages(totalPagesCount);
      setHasMore(page < totalPagesCount);
      setError(null);
    } catch (err) {
      console.error('Error fetching first timers:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [filterInterestType, filterFollowUpStatus, filterConverted]);

  // Load more handler
  const handleLoadMore = useCallback(() => {
    if (!loadingMore && hasMore) {
      const nextPage = currentPage + 1;
      setCurrentPage(nextPage);
      fetchFirstTimers(nextPage, true);
    }
  }, [currentPage, fetchFirstTimers, hasMore, loadingMore]);

  // Infinite scroll hook
  const { sentinelRef } = useInfiniteScroll({
    onLoadMore: handleLoadMore,
    hasMore,
    isLoading: loading || loadingMore,
  });

  const getInterestTypeBadgeClass = (type: string) => {
    switch (type) {
      case 'new_convert':
        return 'bg-green-100 text-green-800';
      case 'visitor':
        return 'bg-blue-100 text-blue-800';
      case 'existing_member':
        return 'bg-purple-100 text-purple-800';
      case 'discipleship':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getFollowUpStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-orange-100 text-orange-800';
      case 'contacted':
        return 'bg-blue-100 text-blue-800';
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800';
      case 'converted':
        return 'bg-green-100 text-green-800';
      case 'lost':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const handleEdit = (firstTimer: FirstTimer) => {
    setSelectedFirstTimer(firstTimer);
    setShowEditModal(true);
  };

  const handleConvert = (firstTimer: FirstTimer) => {
    setSelectedFirstTimer(firstTimer);
    setShowConvertModal(true);
  };

  const handleSuccess = () => {
    fetchStats();
    // Reset and reload
    setFirstTimers([]);
    setCurrentPage(1);
    setHasMore(true);
    fetchFirstTimers(1, false);
  };

  const handleCloseCreateModal = () => {
    setShowCreateModal(false);
    setSelectedFirstTimer(null);
  };

  const handleCloseEditModal = () => {
    setShowEditModal(false);
    setSelectedFirstTimer(null);
  };

  const handleCloseConvertModal = () => {
    setShowConvertModal(false);
    setSelectedFirstTimer(null);
  };

  // Selection handlers
  const handleSelectAll = useCallback((checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(firstTimers.map(ft => ft.id)));
    } else {
      setSelectedIds(new Set());
    }
  }, [firstTimers]);

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
      const response = await axios.post(`${API_ENDPOINTS.FIRST_TIMERS.BASE}/bulk-delete`, {
        ids: Array.from(selectedIds)
      });
      alert(`Successfully deleted ${response.data.deleted_count} first timers`);
      setSelectedIds(new Set());
      setShowDeleteModal(false);
      handleSuccess();
    } catch (err: any) {
      console.error('Failed to delete first timers:', err);
      alert(err.response?.data?.detail || 'Failed to delete first timers');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">First Timer Dashboard</h1>
          <p className="text-gray-600 mt-1">
            {selectedIds.size > 0 ? (
              <span className="text-purple-600 font-medium">{selectedIds.size} selected</span>
            ) : (
              `${firstTimers.length} of ${total} first timers loaded`
            )}
          </p>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          {selectedIds.size > 0 && (
            <button
              onClick={() => setShowDeleteModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-all duration-200"
            >
              <Trash2 className="w-4 h-4" />
              Delete ({selectedIds.size})
            </button>
          )}
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center gap-2 w-full sm:w-auto justify-center"
          >
            <Plus className="w-4 h-4" />
            Add First Timer
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* Total First Timers */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total First Timers</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats.total_first_timers}</p>
              </div>
              <div className="bg-blue-100 p-3 rounded-full">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          {/* This Month */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">This Month</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats.this_month}</p>
              </div>
              <div className="bg-green-100 p-3 rounded-full">
                <Calendar className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          {/* New Converts */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Want Membership</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats.new_converts}</p>
              </div>
              <div className="bg-purple-100 p-3 rounded-full">
                <UserPlus className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>

          {/* Conversion Rate */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Conversion Rate</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stats.conversion_rate}%</p>
              </div>
              <div className="bg-orange-100 p-3 rounded-full">
                <TrendingUp className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Secondary Stats */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">By Interest Type</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Visitors</span>
                <span className="font-semibold">{stats.visitors}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">New Converts</span>
                <span className="font-semibold">{stats.new_converts}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Existing Members</span>
                <span className="font-semibold">{stats.existing_members}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Discipleship</span>
                <span className="font-semibold">{stats.discipleship_interested}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Follow-up Status</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Pending</span>
                <span className="font-semibold text-orange-600">{stats.pending_follow_up}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Contacted</span>
                <span className="font-semibold text-blue-600">{stats.contacted}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">In Progress</span>
                <span className="font-semibold text-yellow-600">{stats.in_progress}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Converted</span>
                <span className="font-semibold text-green-600">{stats.converted}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Recent Activity</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Today</span>
                <span className="font-semibold">{stats.today}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">This Week</span>
                <span className="font-semibold">{stats.this_week}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Converted</span>
                <span className="font-semibold text-green-600">{stats.converted}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Lost</span>
                <span className="font-semibold text-red-600">{stats.lost}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-gray-600" />
          <h3 className="text-sm font-semibold text-gray-700">Filters</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Interest Type</label>
            <select
              value={filterInterestType}
              onChange={(e) => setFilterInterestType(e.target.value)}
              className="input-field"
            >
              <option value="">All Types</option>
              <option value="visitor">Visitor</option>
              <option value="new_convert">New Convert</option>
              <option value="existing_member">Existing Member</option>
              <option value="discipleship">Discipleship</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Follow-up Status</label>
            <select
              value={filterFollowUpStatus}
              onChange={(e) => setFilterFollowUpStatus(e.target.value)}
              className="input-field"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="contacted">Contacted</option>
              <option value="in_progress">In Progress</option>
              <option value="converted">Converted</option>
              <option value="lost">Lost</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Conversion Status</label>
            <select
              value={filterConverted}
              onChange={(e) => setFilterConverted(e.target.value)}
              className="input-field"
            >
              <option value="">All</option>
              <option value="true">Converted</option>
              <option value="false">Not Converted</option>
            </select>
          </div>
        </div>
      </div>

      {/* First Timers List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">First Timers</h3>
        </div>

        {loading && firstTimers.length === 0 ? (
          <div className="p-8 flex flex-col items-center justify-center text-gray-500">
            <Loader className="w-8 h-8 animate-spin mb-2" />
            <span>Loading first timers...</span>
          </div>
        ) : firstTimers.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Users className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p>No first timers found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-4 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={firstTimers.length > 0 && selectedIds.size === firstTimers.length}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Contact
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Visit Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Interest Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Follow-up Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {firstTimers.map((firstTimer) => (
                  <tr
                    key={firstTimer.id}
                    className={`hover:bg-gray-50 cursor-pointer ${selectedIds.has(firstTimer.id) ? 'bg-purple-50' : ''}`}
                  >
                    <td className="px-4 py-4 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selectedIds.has(firstTimer.id)}
                        onChange={(e) => handleSelectOne(firstTimer.id, e.target.checked)}
                        className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap" onClick={() => handleEdit(firstTimer)}>
                      <div className="flex items-center">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{firstTimer.full_name}</div>
                          {firstTimer.converted_to_member && (
                            <div className="flex items-center gap-1 text-xs text-green-600 mt-1">
                              <UserCheck className="w-3 h-3" />
                              <span>Member</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap" onClick={() => handleEdit(firstTimer)}>
                      <div className="text-sm text-gray-900">{firstTimer.phone}</div>
                      {firstTimer.email && (
                        <div className="text-sm text-gray-500">{firstTimer.email}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" onClick={() => handleEdit(firstTimer)}>
                      {formatDate(firstTimer.visit_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap" onClick={() => handleEdit(firstTimer)}>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getInterestTypeBadgeClass(firstTimer.interest_type)}`}>
                        {firstTimer.interest_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap" onClick={() => handleEdit(firstTimer)}>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getFollowUpStatusBadgeClass(firstTimer.follow_up_status)}`}>
                        {firstTimer.follow_up_status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEdit(firstTimer);
                          }}
                          className="p-2 text-gray-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-all"
                          title="View/Edit"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEdit(firstTimer);
                          }}
                          className="p-2 text-gray-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-all"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        {!firstTimer.converted_to_member && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleConvert(firstTimer);
                            }}
                            className="p-2 text-green-600 hover:text-green-700 hover:bg-green-50 rounded-lg transition-all"
                            title="Convert to Member"
                          >
                            <UserCog className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Infinite scroll sentinel and loading indicator */}
            <div ref={sentinelRef} className="py-4">
              {loadingMore && (
                <div className="flex items-center justify-center gap-2 text-gray-500">
                  <Loader className="h-5 w-5 animate-spin" />
                  <span>Loading more first timers...</span>
                </div>
              )}
              {!hasMore && firstTimers.length > 0 && (
                <p className="text-center text-gray-500 text-sm">
                  All {total} first timers loaded
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <FirstTimerFormModal
        isOpen={showCreateModal}
        onClose={handleCloseCreateModal}
        onSuccess={handleSuccess}
      />

      <FirstTimerFormModal
        isOpen={showEditModal}
        onClose={handleCloseEditModal}
        onSuccess={handleSuccess}
        editingFirstTimer={selectedFirstTimer}
      />

      <ConvertToMemberModal
        isOpen={showConvertModal}
        onClose={handleCloseConvertModal}
        onSuccess={handleSuccess}
        firstTimer={selectedFirstTimer}
      />

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full">
            <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4 flex items-center justify-between rounded-t-2xl">
              <div className="flex items-center gap-3">
                <Trash2 className="w-6 h-6 text-white" />
                <h2 className="text-xl font-semibold text-white">Delete First Timers</h2>
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
                Are you sure you want to delete <span className="font-bold text-red-600">{selectedIds.size}</span> selected first timer{selectedIds.size > 1 ? 's' : ''}?
              </p>
              <p className="text-sm text-gray-500 mb-6">
                This action will remove these first timers from active lists. This cannot be undone.
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
};

export default FirstTimerDashboard;
