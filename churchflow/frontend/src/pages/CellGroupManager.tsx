/**
 * Cell Group Manager Page
 *
 * CRUD operations for cell groups including:
 * - List all cell groups
 * - Create new cell groups
 * - Edit cell group details
 * - Assign cell leaders
 * - View cell members
 *
 * URL: /cell-groups
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Plus,
  Edit,
  Trash2,
  UserPlus,
  MapPin,
  Calendar,
  Clock,
  Loader,
  AlertCircle,
  CheckCircle,
  X,
  Search,
  Filter,
} from 'lucide-react';
import { cellGroupApi, zoneApi, type CellGroup, type Zone } from '../services/visitorApi';

interface CellGroupFormData {
  name: string;
  description: string;
  zone_id: string;
  meeting_day: string;
  meeting_time: string;
  meeting_location: string;
  target_size: number;
}

export default function CellGroupManager() {
  const navigate = useNavigate();
  const [cellGroups, setCellGroups] = useState<CellGroup[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [filteredGroups, setFilteredGroups] = useState<CellGroup[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [zoneFilter, setZoneFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('active');
  const [formData, setFormData] = useState<CellGroupFormData>({
    name: '',
    description: '',
    zone_id: '',
    meeting_day: '',
    meeting_time: '',
    meeting_location: '',
    target_size: 12,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    filterCellGroups();
  }, [cellGroups, searchQuery, zoneFilter, statusFilter]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [groupsData, zonesData] = await Promise.all([
        cellGroupApi.getCellGroups({}),
        zoneApi.getZones(),
      ]);
      setCellGroups(groupsData.cell_groups);
      setZones(zonesData.zones);
    } catch (err: any) {
      console.error('Failed to load data:', err);
      setError(err.response?.data?.detail || 'Failed to load cell groups');
    } finally {
      setIsLoading(false);
    }
  };

  const filterCellGroups = () => {
    let filtered = cellGroups;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (group) =>
          group.name.toLowerCase().includes(query) ||
          group.description?.toLowerCase().includes(query) ||
          group.meeting_location?.toLowerCase().includes(query)
      );
    }

    // Zone filter
    if (zoneFilter !== 'all') {
      filtered = filtered.filter((group) => group.zone_id === zoneFilter);
    }

    // Status filter
    if (statusFilter === 'active') {
      filtered = filtered.filter((group) => group.is_active);
    } else if (statusFilter === 'inactive') {
      filtered = filtered.filter((group) => !group.is_active);
    }

    setFilteredGroups(filtered);
  };

  const handleCreateCellGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);

    try {
      await cellGroupApi.createCellGroup({
        name: formData.name,
        description: formData.description || undefined,
        zone_id: formData.zone_id || undefined,
        meeting_day: formData.meeting_day || undefined,
        meeting_time: formData.meeting_time || undefined,
        meeting_location: formData.meeting_location || undefined,
      });

      setShowCreateModal(false);
      setFormData({
        name: '',
        description: '',
        zone_id: '',
        meeting_day: '',
        meeting_time: '',
        meeting_location: '',
        target_size: 12,
      });
      await loadData();
    } catch (err: any) {
      console.error('Failed to create cell group:', err);
      setFormError(err.response?.data?.detail || 'Failed to create cell group');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewMembers = (cellGroupId: string) => {
    navigate(`/cell-groups/${cellGroupId}/members`);
  };

  const getZoneName = (zoneId?: string) => {
    if (!zoneId) return 'No Zone';
    const zone = zones.find((z) => z.id === zoneId);
    return zone?.name || 'Unknown Zone';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Users className="w-6 h-6 text-purple-600" />
                Cell Groups
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                {filteredGroups.length} {filteredGroups.length === 1 ? 'group' : 'groups'}
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
            >
              <Plus className="w-5 h-5" />
              Create Cell Group
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search cell groups..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <select
              value={zoneFilter}
              onChange={(e) => setZoneFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="all">All Zones</option>
              {zones.map((zone) => (
                <option key={zone.id} value={zone.id}>
                  {zone.name}
                </option>
              ))}
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="all">All Statuses</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-semibold text-red-900">Error</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader className="w-8 h-8 text-purple-600 animate-spin mb-4" />
            <p className="text-gray-600">Loading cell groups...</p>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && filteredGroups.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Cell Groups Found</h3>
            <p className="text-gray-600 mb-6">
              {searchQuery
                ? 'Try adjusting your search or filters'
                : 'Create your first cell group to get started'}
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
            >
              <Plus className="w-5 h-5" />
              Create Cell Group
            </button>
          </div>
        )}

        {/* Cell Groups Grid */}
        {!isLoading && filteredGroups.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredGroups.map((group) => (
              <div
                key={group.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 text-lg mb-1">{group.name}</h3>
                    <span className="text-sm text-purple-600">{getZoneName(group.zone_id)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    {group.is_full && (
                      <span className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-orange-100 text-orange-800">
                        Full
                      </span>
                    )}
                    {!group.is_active && (
                      <span className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                        Inactive
                      </span>
                    )}
                  </div>
                </div>

                {group.description && (
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">{group.description}</p>
                )}

                <div className="space-y-2 mb-4">
                  {group.meeting_day && group.meeting_time && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Calendar className="w-4 h-4 flex-shrink-0" />
                      <span>
                        {group.meeting_day} at {group.meeting_time}
                      </span>
                    </div>
                  )}
                  {group.meeting_location && (
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <MapPin className="w-4 h-4 flex-shrink-0" />
                      <span className="truncate">{group.meeting_location}</span>
                    </div>
                  )}
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <div className="flex items-center justify-between text-sm mb-4">
                    <span className="text-gray-500">Members:</span>
                    <span className="font-semibold text-gray-900">
                      {group.current_member_count} / {group.target_size}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                    <div
                      className="bg-purple-600 h-2 rounded-full"
                      style={{
                        width: `${Math.min(
                          (group.current_member_count / group.target_size) * 100,
                          100
                        )}%`,
                      }}
                    ></div>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleViewMembers(group.id)}
                    className="flex-1 px-3 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium flex items-center justify-center gap-1"
                  >
                    <Users className="w-4 h-4" />
                    Members
                  </button>
                  <button
                    onClick={() => navigate(`/cell-groups/${group.id}/edit`)}
                    className="px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Cell Group Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">Create Cell Group</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <form onSubmit={handleCreateCellGroup} className="p-6 space-y-6">
              {formError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-sm text-red-700">{formError}</p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cell Group Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="e.g., Sunrise Cell Group"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Describe the cell group..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Zone</label>
                <select
                  value={formData.zone_id}
                  onChange={(e) => setFormData({ ...formData, zone_id: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="">No Zone</option>
                  {zones.map((zone) => (
                    <option key={zone.id} value={zone.id}>
                      {zone.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Meeting Day</label>
                  <select
                    value={formData.meeting_day}
                    onChange={(e) => setFormData({ ...formData, meeting_day: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    <option value="">Select Day</option>
                    {weekDays.map((day) => (
                      <option key={day} value={day}>
                        {day}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Meeting Time</label>
                  <input
                    type="time"
                    value={formData.meeting_time}
                    onChange={(e) => setFormData({ ...formData, meeting_time: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Meeting Location</label>
                <input
                  type="text"
                  value={formData.meeting_location}
                  onChange={(e) => setFormData({ ...formData, meeting_location: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="123 Main Street, Accra"
                />
              </div>

              <div className="flex gap-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:bg-purple-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <Loader className="w-5 h-5 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Plus className="w-5 h-5" />
                      Create Cell Group
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
