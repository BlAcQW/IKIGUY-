/**
 * Register Existing Member Modal
 *
 * Allows admins to register existing church members who are not yet in the system.
 * These are established members who didn't go through the first-timer flow.
 */

import React, { useState, useEffect } from 'react';
import { X, UserPlus, Loader2, AlertCircle } from 'lucide-react';
import { API_ENDPOINTS, getApiUrl } from '../../config/api-config';
import { encodeHeaderValue } from '../../lib/header-utils';

interface Branch {
  id: string;
  name: string;
}

interface Subgroup {
  id: string;
  name: string;
  group_id: string;
}

interface Group {
  id: string;
  name: string;
  subgroups?: Subgroup[];
}

interface MemberFormData {
  full_name: string;
  phone: string;
  email: string;
  branch_id: string;
  gender: string;
  date_of_birth: string;
  address: string;
  occupation: string;
  marital_status: string;
  group_ids: string[];
  subgroup_ids: string[];
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const RegisterExistingMemberModal: React.FC<Props> = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState<MemberFormData>({
    full_name: '',
    phone: '',
    email: '',
    branch_id: '',
    gender: '',
    date_of_birth: '',
    address: '',
    occupation: '',
    marital_status: '',
    group_ids: [],
    subgroup_ids: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loadingBranches, setLoadingBranches] = useState(true);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loadingGroups, setLoadingGroups] = useState(true);

  // Fetch branches and groups on mount
  useEffect(() => {
    const fetchBranches = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const orgId = localStorage.getItem('current_organization_id');

        const response = await fetch(getApiUrl('branches'), {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Organization-ID': encodeHeaderValue(orgId) || '',
          },
        });

        if (response.ok) {
          const data = await response.json();
          // Handle both array response and paginated response
          const branchList = Array.isArray(data) ? data : (data.items || data.branches || []);
          setBranches(branchList.map((b: any) => ({
            id: b.id || b._id,
            name: b.name,
          })));
        }
      } catch (err) {
        console.error('Failed to fetch branches:', err);
      } finally {
        setLoadingBranches(false);
      }
    };

    const fetchGroups = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const orgId = localStorage.getItem('current_organization_id');

        const response = await fetch(getApiUrl('groups'), {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Organization-ID': encodeHeaderValue(orgId) || '',
          },
        });

        if (response.ok) {
          const data = await response.json();
          const groupList = Array.isArray(data) ? data : (data.items || data.groups || []);

          // For each group, fetch its subgroups
          const groupsWithSubgroups = await Promise.all(
            groupList.map(async (g: any) => {
              const groupId = g.id || g._id;
              try {
                const subgroupsResponse = await fetch(getApiUrl(`groups/${groupId}`), {
                  headers: {
                    'Authorization': `Bearer ${token}`,
                    'X-Organization-ID': encodeHeaderValue(orgId) || '',
                  },
                });
                if (subgroupsResponse.ok) {
                  const groupWithSubgroups = await subgroupsResponse.json();
                  return {
                    id: groupId,
                    name: g.name,
                    subgroups: (groupWithSubgroups.subgroups || []).map((s: any) => ({
                      id: s.id || s._id,
                      name: s.name,
                      group_id: groupId,
                    })),
                  };
                }
              } catch {
                // If subgroups fetch fails, return group without subgroups
              }
              return {
                id: groupId,
                name: g.name,
                subgroups: [],
              };
            })
          );

          setGroups(groupsWithSubgroups);
        }
      } catch (err) {
        console.error('Failed to fetch groups:', err);
      } finally {
        setLoadingGroups(false);
      }
    };

    if (isOpen) {
      fetchBranches();
      fetchGroups();
      // Reset form when opening
      setFormData({
        full_name: '',
        phone: '',
        email: '',
        branch_id: '',
        gender: '',
        date_of_birth: '',
        address: '',
        occupation: '',
        marital_status: '',
        group_ids: [],
        subgroup_ids: [],
      });
      setError(null);
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const orgId = localStorage.getItem('current_organization_id');

      // Prepare data - remove empty strings
      const dataToSend: any = {
        full_name: formData.full_name.trim(),
        phone: formData.phone.trim(),
        branch_id: formData.branch_id,
        roles: ['member'],
      };

      // Add optional fields if provided
      if (formData.email.trim()) dataToSend.email = formData.email.trim();
      if (formData.gender) dataToSend.gender = formData.gender;
      if (formData.address.trim()) dataToSend.address = formData.address.trim();
      if (formData.occupation.trim()) dataToSend.occupation = formData.occupation.trim();
      if (formData.marital_status) dataToSend.marital_status = formData.marital_status;

      // Add groups and subgroups if selected
      if (formData.group_ids.length > 0) dataToSend.group_ids = formData.group_ids;
      if (formData.subgroup_ids.length > 0) dataToSend.subgroup_ids = formData.subgroup_ids;

      // Convert date to ISO format if provided
      if (formData.date_of_birth) {
        dataToSend.date_of_birth = new Date(formData.date_of_birth).toISOString();
      }

      const response = await fetch(API_ENDPOINTS.USERS.REGISTER_EXISTING_MEMBER, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'X-Organization-ID': encodeHeaderValue(orgId) || '',
        },
        body: JSON.stringify(dataToSend),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to register member');
      }

      onSuccess();
      onClose();
    } catch (err) {
      console.error('Error registering member:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full sm:max-w-2xl max-h-[90vh] overflow-hidden transform transition-all duration-200 my-8">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/20 rounded-xl">
                <UserPlus className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Register Existing Member</h2>
                <p className="text-green-100 text-sm mt-0.5">
                  Add an established member to the system
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-xl transition-colors"
            >
              <X className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-red-800 font-medium">Registration Failed</p>
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            </div>
          )}

          <div className="space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
                Basic Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                    placeholder="Enter member's full name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    required
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                    placeholder="+233..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                    placeholder="email@example.com"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Branch <span className="text-red-500">*</span>
                  </label>
                  {loadingBranches ? (
                    <div className="flex items-center gap-2 text-gray-500 py-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Loading branches...</span>
                    </div>
                  ) : (
                    <select
                      required
                      value={formData.branch_id}
                      onChange={(e) => setFormData({ ...formData, branch_id: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                    >
                      <option value="">Select a branch</option>
                      {branches.map((branch) => (
                        <option key={branch.id} value={branch.id}>
                          {branch.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>
            </div>

            {/* Demographics */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
                Demographics (Optional)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gender
                  </label>
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                    <option value="prefer_not_to_say">Prefer not to say</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    value={formData.date_of_birth}
                    onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Marital Status
                  </label>
                  <select
                    value={formData.marital_status}
                    onChange={(e) => setFormData({ ...formData, marital_status: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                  >
                    <option value="">Select status</option>
                    <option value="single">Single</option>
                    <option value="married">Married</option>
                    <option value="divorced">Divorced</option>
                    <option value="widowed">Widowed</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Occupation
                  </label>
                  <input
                    type="text"
                    value={formData.occupation}
                    onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
                    placeholder="e.g. Teacher, Engineer, etc."
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Address
                  </label>
                  <textarea
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    rows={2}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors resize-none"
                    placeholder="Physical address"
                  />
                </div>
              </div>
            </div>

            {/* Groups & Subgroups */}
            <div>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
                Groups & Subgroups (Optional)
              </h3>
              {loadingGroups ? (
                <div className="flex items-center gap-2 text-gray-500 py-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Loading groups...</span>
                </div>
              ) : groups.length === 0 ? (
                <p className="text-gray-500 text-sm">No groups available</p>
              ) : (
                <div className="space-y-4">
                  {groups.map((group) => (
                    <div key={group.id} className="border border-gray-200 rounded-xl p-4">
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.group_ids.includes(group.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({
                                ...formData,
                                group_ids: [...formData.group_ids, group.id],
                              });
                            } else {
                              // Remove group and its subgroups
                              const groupSubgroupIds = (group.subgroups || []).map(s => s.id);
                              setFormData({
                                ...formData,
                                group_ids: formData.group_ids.filter(id => id !== group.id),
                                subgroup_ids: formData.subgroup_ids.filter(id => !groupSubgroupIds.includes(id)),
                              });
                            }
                          }}
                          className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                        />
                        <span className="font-medium text-gray-800">{group.name}</span>
                      </label>

                      {/* Show subgroups if group is selected and has subgroups */}
                      {formData.group_ids.includes(group.id) && group.subgroups && group.subgroups.length > 0 && (
                        <div className="mt-3 ml-7 space-y-2">
                          <p className="text-xs text-gray-500 uppercase font-medium">Subgroups:</p>
                          <div className="grid grid-cols-2 gap-2">
                            {group.subgroups.map((subgroup) => (
                              <label key={subgroup.id} className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={formData.subgroup_ids.includes(subgroup.id)}
                                  onChange={(e) => {
                                    if (e.target.checked) {
                                      setFormData({
                                        ...formData,
                                        subgroup_ids: [...formData.subgroup_ids, subgroup.id],
                                      });
                                    } else {
                                      setFormData({
                                        ...formData,
                                        subgroup_ids: formData.subgroup_ids.filter(id => id !== subgroup.id),
                                      });
                                    }
                                  }}
                                  className="w-3.5 h-3.5 text-green-600 border-gray-300 rounded focus:ring-green-500"
                                />
                                <span className="text-sm text-gray-700">{subgroup.name}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || loadingBranches || loadingGroups}
              className="px-5 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Registering...
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  Register Member
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RegisterExistingMemberModal;
