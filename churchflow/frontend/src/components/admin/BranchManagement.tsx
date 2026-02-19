/**
 * Branch Management Admin Component
 *
 * Complete CRUD interface for managing church branches with geolocation support.
 * Allows admins to:
 * - Create/edit/delete branches
 * - Set GPS coordinates using map picker
 * - Configure auto check-in radius
 * - Manage service schedules
 * - View branch statistics
 */

import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  Info,
  CheckCircle,
  AlertCircle,
  Clock,
  Navigation,
  Settings
} from 'lucide-react';
import MapPicker from '../MapPicker';
import { useOrganization } from '../../hooks/useOrganization';

// Types
interface ServiceSchedule {
  day_of_week: string;
  service_type: string;
  start_time: string;
  duration_minutes: number;
  is_active: boolean;
}

interface Branch {
  _id: string;
  organization_id: string;
  name: string;
  location: string;
  region: string;
  latitude: number | null;
  longitude: number | null;
  checkin_radius: number;
  auto_checkin_enabled: boolean;
  geocoding_accuracy: string | null;
  service_times: ServiceSchedule[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  has_coordinates: boolean;
  can_auto_checkin: boolean;
}

interface BranchStats {
  total_branches: number;
  active_branches: number;
  inactive_branches: number;
  with_coordinates: number;
  without_coordinates: number;
  auto_checkin_enabled: number;
  by_region: Record<string, number>;
}

export default function BranchManagement() {
  const { currentOrganization } = useOrganization();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [stats, setStats] = useState<BranchStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingBranch, setEditingBranch] = useState<Branch | null>(null);
  const [filterRegion, setFilterRegion] = useState<string>('');
  const [showActiveOnly, setShowActiveOnly] = useState(true);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    region: '',
    latitude: null as number | null,
    longitude: null as number | null,
    checkin_radius: 500,
    auto_checkin_enabled: false,
    service_times: [] as ServiceSchedule[],
    is_active: true
  });

  // Fetch branches
  const fetchBranches = async () => {
    if (!currentOrganization) return;

    setLoading(true);
    try {
      const params = new URLSearchParams({
        organization_id: currentOrganization._id,
        ...(showActiveOnly && { is_active: 'true' }),
        ...(filterRegion && { region: filterRegion }),
        limit: '500'
      });

      const response = await fetch(`/api/v1/branches?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch branches');

      const data = await response.json();
      setBranches(data);
    } catch (error) {
      console.error('Error fetching branches:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch statistics
  const fetchStats = async () => {
    if (!currentOrganization) return;

    try {
      const response = await fetch(
        `/api/v1/branches/stats/summary?organization_id=${currentOrganization._id}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      if (!response.ok) throw new Error('Failed to fetch stats');

      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  useEffect(() => {
    fetchBranches();
    fetchStats();
  }, [currentOrganization, showActiveOnly, filterRegion]);

  // Open create modal
  const handleCreate = () => {
    setEditingBranch(null);
    setFormData({
      name: '',
      location: '',
      region: '',
      latitude: null,
      longitude: null,
      checkin_radius: 500,
      auto_checkin_enabled: false,
      service_times: [],
      is_active: true
    });
    setShowModal(true);
  };

  // Open edit modal
  const handleEdit = (branch: Branch) => {
    setEditingBranch(branch);
    setFormData({
      name: branch.name,
      location: branch.location,
      region: branch.region,
      latitude: branch.latitude,
      longitude: branch.longitude,
      checkin_radius: branch.checkin_radius,
      auto_checkin_enabled: branch.auto_checkin_enabled,
      service_times: branch.service_times,
      is_active: branch.is_active
    });
    setShowModal(true);
  };

  // Save branch (create or update)
  const handleSave = async () => {
    if (!currentOrganization) return;

    try {
      const payload = {
        ...formData,
        organization_id: currentOrganization._id
      };

      const url = editingBranch
        ? `/api/v1/branches/${editingBranch._id}`
        : '/api/v1/branches';

      const method = editingBranch ? 'PATCH' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save branch');
      }

      setShowModal(false);
      fetchBranches();
      fetchStats();
    } catch (error: any) {
      console.error('Error saving branch:', error);
      alert(error.message);
    }
  };

  // Delete branch
  const handleDelete = async (branchId: string) => {
    if (!confirm('Are you sure you want to delete this branch? This will deactivate it (soft delete).')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/branches/${branchId}?soft_delete=true`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (!response.ok) throw new Error('Failed to delete branch');

      fetchBranches();
      fetchStats();
    } catch (error) {
      console.error('Error deleting branch:', error);
      alert('Failed to delete branch');
    }
  };

  // Handle map coordinates selection
  const handleCoordinatesSelected = (lat: number, lon: number) => {
    setFormData(prev => ({
      ...prev,
      latitude: lat,
      longitude: lon
    }));
  };

  // Get unique regions
  const regions = Array.from(new Set(branches.map(b => b.region))).sort();

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Branch Management</h1>
        <p className="text-gray-600">
          Manage church branches with geolocation settings for auto check-in
        </p>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">Total Branches</div>
            <div className="text-2xl font-bold text-purple-600">{stats.total_branches}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">Active</div>
            <div className="text-2xl font-bold text-green-600">{stats.active_branches}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">With GPS</div>
            <div className="text-2xl font-bold text-blue-600">{stats.with_coordinates}</div>
            <div className="text-xs text-gray-500">
              {Math.round((stats.with_coordinates / stats.total_branches) * 100)}%
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">Auto Check-In</div>
            <div className="text-2xl font-bold text-indigo-600">{stats.auto_checkin_enabled}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">Need GPS</div>
            <div className="text-2xl font-bold text-orange-600">{stats.without_coordinates}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">Inactive</div>
            <div className="text-2xl font-bold text-gray-600">{stats.inactive_branches}</div>
          </div>
        </div>
      )}

      {/* Toolbar */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Region Filter */}
            <select
              value={filterRegion}
              onChange={(e) => setFilterRegion(e.target.value)}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600"
            >
              <option value="">All Regions</option>
              {regions.map(region => (
                <option key={region} value={region}>{region}</option>
              ))}
            </select>

            {/* Active Filter */}
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showActiveOnly}
                onChange={(e) => setShowActiveOnly(e.target.checked)}
                className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
              />
              <span>Show active only</span>
            </label>
          </div>

          {/* Create Button */}
          <button
            onClick={handleCreate}
            className="flex items-center space-x-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
          >
            <Plus className="h-5 w-5" />
            <span>Create Branch</span>
          </button>
        </div>
      </div>

      {/* Branch List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Branch
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Region
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                GPS
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Auto Check-In
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Radius
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                  Loading branches...
                </td>
              </tr>
            ) : branches.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                  No branches found
                </td>
              </tr>
            ) : (
              branches.map((branch) => (
                <tr key={branch._id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium text-gray-900">{branch.name}</div>
                      <div className="text-sm text-gray-500">{branch.location}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {branch.region}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {branch.has_coordinates ? (
                      <div className="flex flex-col items-center">
                        <CheckCircle className="h-5 w-5 text-green-500 mb-1" />
                        <span className="text-xs text-gray-500">
                          {branch.latitude?.toFixed(4)}, {branch.longitude?.toFixed(4)}
                        </span>
                      </div>
                    ) : (
                      <AlertCircle className="h-5 w-5 text-orange-500 mx-auto" />
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">
                    {branch.auto_checkin_enabled ? (
                      <Navigation className="h-5 w-5 text-blue-500 mx-auto" />
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center text-sm text-gray-900">
                    {branch.checkin_radius}m
                  </td>
                  <td className="px-6 py-4 text-center">
                    {branch.is_active ? (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center space-x-2">
                      <button
                        onClick={() => handleEdit(branch)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition"
                        title="Edit"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(branch._id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold">
                  {editingBranch ? 'Edit Branch' : 'Create Branch'}
                </h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-6">
                {/* Basic Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Branch Name *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600"
                      placeholder="e.g., Adenta"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Region *
                    </label>
                    <input
                      type="text"
                      value={formData.region}
                      onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600"
                      placeholder="e.g., Greater Accra"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Location Description *
                  </label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600"
                    placeholder="e.g., Adenta, Greater Accra, Ghana"
                    required
                  />
                </div>

                {/* GPS Coordinates */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    GPS Coordinates
                  </label>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <MapPicker
                      initialLat={formData.latitude || 5.6037}
                      initialLon={formData.longitude || -0.1870}
                      onCoordinatesSelected={handleCoordinatesSelected}
                    />
                    {formData.latitude && formData.longitude && (
                      <div className="mt-3 text-sm text-gray-600">
                        <MapPin className="inline h-4 w-4 mr-1" />
                        Selected: {formData.latitude.toFixed(6)}, {formData.longitude.toFixed(6)}
                      </div>
                    )}
                  </div>
                </div>

                {/* Check-in Settings */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Check-in Radius (meters)
                    </label>
                    <input
                      type="number"
                      value={formData.checkin_radius}
                      onChange={(e) => setFormData({ ...formData, checkin_radius: parseInt(e.target.value) })}
                      min="50"
                      max="5000"
                      step="50"
                      className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-600"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Distance from branch for auto check-in (50-5000m)
                    </p>
                  </div>

                  <div className="space-y-3 pt-7">
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={formData.auto_checkin_enabled}
                        onChange={(e) => setFormData({ ...formData, auto_checkin_enabled: e.target.checked })}
                        className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                      />
                      <span className="text-sm font-medium">Enable auto check-in</span>
                    </label>

                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={formData.is_active}
                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                        className="w-5 h-5 text-purple-600 rounded focus:ring-purple-500"
                      />
                      <span className="text-sm font-medium">Active branch</span>
                    </label>
                  </div>
                </div>

                {/* Info Box */}
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div className="text-sm text-blue-800">
                      <p className="font-medium mb-1">About Auto Check-In</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Members will be prompted to check in when within the radius</li>
                        <li>GPS coordinates are required for auto check-in to work</li>
                        <li>Recommended radius: 500m for urban areas, 1000m for suburban</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end space-x-4 mt-8">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="flex items-center space-x-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                >
                  <Save className="h-5 w-5" />
                  <span>{editingBranch ? 'Update' : 'Create'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
