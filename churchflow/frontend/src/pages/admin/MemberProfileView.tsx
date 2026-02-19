/**
 * Member Profile View Page
 *
 * Admin view for viewing and editing member profiles.
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, User, Phone, Mail, MapPin, Briefcase, Heart,
  Calendar, Edit2, Save, X, Loader2, Shield, Users as UsersIcon, Building
} from 'lucide-react';
import { getApiUrl } from '../../config/api-config';
import { encodeHeaderValue } from '../../lib/header-utils';

interface MemberProfile {
  id: string;
  full_name?: string;
  name?: string;
  phone: string;
  email?: string;
  date_of_birth?: string;
  gender?: string;
  address?: string;
  city?: string;
  occupation?: string;
  marital_status?: string;
  spouse_name?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  branch_id?: string;
  branch_name?: string;
  roles?: string[];
  member_status?: string;
  group_ids?: string[];
  subgroup_ids?: string[];
  created_at?: string;
  updated_at?: string;
}

interface Branch {
  id: string;
  name: string;
}

interface Group {
  id: string;
  name: string;
  subgroups?: Subgroup[];
}

interface Subgroup {
  id: string;
  name: string;
  group_id: string;
}

export default function MemberProfileView() {
  const { memberId } = useParams<{ memberId: string }>();
  const navigate = useNavigate();

  const [member, setMember] = useState<MemberProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState<Partial<MemberProfile>>({});
  const [branches, setBranches] = useState<Branch[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);

  useEffect(() => {
    fetchMember();
    fetchBranches();
    fetchGroups();
  }, [memberId]);

  const fetchMember = async () => {
    if (!memberId) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const orgId = localStorage.getItem('current_organization_id');

      const response = await fetch(getApiUrl(`visitors/${memberId}`), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Organization-ID': encodeHeaderValue(orgId) || '',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch member');
      }

      const data = await response.json();
      setMember(data);
      setFormData(data);
    } catch (err) {
      console.error('Error fetching member:', err);
      setError(err instanceof Error ? err.message : 'Failed to load member profile');
    } finally {
      setLoading(false);
    }
  };

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
        const branchList = Array.isArray(data) ? data : (data.items || data.branches || []);
        setBranches(branchList.map((b: any) => ({ id: b.id || b._id, name: b.name })));
      }
    } catch (err) {
      console.error('Failed to fetch branches:', err);
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

        // Fetch subgroups for each group
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
              // Ignore
            }
            return { id: groupId, name: g.name, subgroups: [] };
          })
        );

        setGroups(groupsWithSubgroups);
      }
    } catch (err) {
      console.error('Failed to fetch groups:', err);
    }
  };

  const handleSave = async () => {
    if (!memberId) return;

    setSaving(true);

    try {
      const token = localStorage.getItem('access_token');
      const orgId = localStorage.getItem('current_organization_id');

      const response = await fetch(getApiUrl(`visitors/${memberId}`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'X-Organization-ID': encodeHeaderValue(orgId) || '',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Failed to update member');
      }

      const updatedMember = await response.json();
      setMember(updatedMember);
      setIsEditing(false);
    } catch (err) {
      console.error('Error updating member:', err);
      setError(err instanceof Error ? err.message : 'Failed to update member');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setFormData(member || {});
    setIsEditing(false);
  };

  const handleGroupToggle = (groupId: string) => {
    const currentGroups = formData.group_ids || [];
    if (currentGroups.includes(groupId)) {
      // Remove group and its subgroups
      const group = groups.find(g => g.id === groupId);
      const groupSubgroupIds = (group?.subgroups || []).map(s => s.id);
      setFormData({
        ...formData,
        group_ids: currentGroups.filter(id => id !== groupId),
        subgroup_ids: (formData.subgroup_ids || []).filter(id => !groupSubgroupIds.includes(id)),
      });
    } else {
      setFormData({
        ...formData,
        group_ids: [...currentGroups, groupId],
      });
    }
  };

  const handleSubgroupToggle = (subgroupId: string) => {
    const currentSubgroups = formData.subgroup_ids || [];
    if (currentSubgroups.includes(subgroupId)) {
      setFormData({
        ...formData,
        subgroup_ids: currentSubgroups.filter(id => id !== subgroupId),
      });
    } else {
      setFormData({
        ...formData,
        subgroup_ids: [...currentSubgroups, subgroupId],
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
        <span className="ml-3 text-gray-600">Loading member profile...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-800 font-medium">Error loading profile</p>
          <p className="text-red-600 text-sm mt-1">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!member) {
    return (
      <div className="p-8">
        <div className="text-center py-12">
          <User className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Member not found</p>
          <button
            onClick={() => navigate(-1)}
            className="mt-4 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-100 rounded-xl transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Member Profile</h1>
            <p className="text-gray-500 text-sm">View and edit member information</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isEditing ? (
            <>
              <button
                onClick={handleCancel}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors flex items-center gap-2"
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {saving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                Save Changes
              </button>
            </>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors flex items-center gap-2"
            >
              <Edit2 className="w-4 h-4" />
              Edit Profile
            </button>
          )}
        </div>
      </div>

      {/* Profile Card */}
      <div className="bg-white rounded-2xl shadow-sm border p-6 mb-6">
        {/* Avatar and Name */}
        <div className="flex items-center gap-4 mb-6 pb-6 border-b">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
            <span className="text-2xl font-bold text-white">
              {(member.full_name || member.name || '?').charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            {isEditing ? (
              <input
                type="text"
                value={formData.full_name || formData.name || ''}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="text-2xl font-bold text-gray-900 border-b-2 border-purple-300 focus:border-purple-500 outline-none bg-transparent"
                placeholder="Full Name"
              />
            ) : (
              <h2 className="text-2xl font-bold text-gray-900">{member.full_name || member.name || 'Unknown'}</h2>
            )}
            <div className="flex items-center gap-3 mt-1">
              {member.roles && member.roles.length > 0 && (
                <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-700 rounded-full flex items-center gap-1">
                  <Shield className="w-3 h-3" />
                  {member.roles.join(', ')}
                </span>
              )}
              {member.member_status && (
                <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full">
                  {member.member_status}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Contact Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Phone */}
          <div className="flex items-start gap-3">
            <Phone className="w-5 h-5 text-gray-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-gray-500">Phone</p>
              {isEditing ? (
                <input
                  type="tel"
                  value={formData.phone || ''}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full font-medium text-gray-900 border-b border-gray-200 focus:border-purple-500 outline-none py-1"
                />
              ) : (
                <p className="font-medium text-gray-900">{member.phone}</p>
              )}
            </div>
          </div>

          {/* Email */}
          <div className="flex items-start gap-3">
            <Mail className="w-5 h-5 text-gray-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-gray-500">Email</p>
              {isEditing ? (
                <input
                  type="email"
                  value={formData.email || ''}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full font-medium text-gray-900 border-b border-gray-200 focus:border-purple-500 outline-none py-1"
                  placeholder="Not provided"
                />
              ) : (
                <p className="font-medium text-gray-900">{member.email || 'Not provided'}</p>
              )}
            </div>
          </div>

          {/* Date of Birth */}
          <div className="flex items-start gap-3">
            <Calendar className="w-5 h-5 text-gray-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-gray-500">Date of Birth</p>
              {isEditing ? (
                <input
                  type="date"
                  value={formData.date_of_birth?.split('T')[0] || ''}
                  onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                  className="w-full font-medium text-gray-900 border-b border-gray-200 focus:border-purple-500 outline-none py-1"
                />
              ) : (
                <p className="font-medium text-gray-900">
                  {member.date_of_birth ? new Date(member.date_of_birth).toLocaleDateString() : 'Not provided'}
                </p>
              )}
            </div>
          </div>

          {/* Gender */}
          <div className="flex items-start gap-3">
            <User className="w-5 h-5 text-gray-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-gray-500">Gender</p>
              {isEditing ? (
                <select
                  value={formData.gender || ''}
                  onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                  className="w-full font-medium text-gray-900 border-b border-gray-200 focus:border-purple-500 outline-none py-1 bg-transparent"
                >
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              ) : (
                <p className="font-medium text-gray-900 capitalize">{member.gender || 'Not provided'}</p>
              )}
            </div>
          </div>

          {/* Address */}
          <div className="flex items-start gap-3 md:col-span-2">
            <MapPin className="w-5 h-5 text-gray-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-gray-500">Address</p>
              {isEditing ? (
                <input
                  type="text"
                  value={formData.address || ''}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full font-medium text-gray-900 border-b border-gray-200 focus:border-purple-500 outline-none py-1"
                  placeholder="Not provided"
                />
              ) : (
                <p className="font-medium text-gray-900">{member.address || 'Not provided'}</p>
              )}
            </div>
          </div>

          {/* Occupation */}
          <div className="flex items-start gap-3">
            <Briefcase className="w-5 h-5 text-gray-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-gray-500">Occupation</p>
              {isEditing ? (
                <input
                  type="text"
                  value={formData.occupation || ''}
                  onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                  className="w-full font-medium text-gray-900 border-b border-gray-200 focus:border-purple-500 outline-none py-1"
                  placeholder="Not provided"
                />
              ) : (
                <p className="font-medium text-gray-900">{member.occupation || 'Not provided'}</p>
              )}
            </div>
          </div>

          {/* Marital Status */}
          <div className="flex items-start gap-3">
            <Heart className="w-5 h-5 text-gray-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-gray-500">Marital Status</p>
              {isEditing ? (
                <select
                  value={formData.marital_status || ''}
                  onChange={(e) => setFormData({ ...formData, marital_status: e.target.value })}
                  className="w-full font-medium text-gray-900 border-b border-gray-200 focus:border-purple-500 outline-none py-1 bg-transparent"
                >
                  <option value="">Select status</option>
                  <option value="single">Single</option>
                  <option value="married">Married</option>
                  <option value="divorced">Divorced</option>
                  <option value="widowed">Widowed</option>
                </select>
              ) : (
                <p className="font-medium text-gray-900 capitalize">{member.marital_status || 'Not provided'}</p>
              )}
            </div>
          </div>

          {/* Branch */}
          <div className="flex items-start gap-3 md:col-span-2">
            <Building className="w-5 h-5 text-gray-400 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-gray-500">Branch</p>
              {isEditing ? (
                <select
                  value={formData.branch_id || ''}
                  onChange={(e) => setFormData({ ...formData, branch_id: e.target.value })}
                  className="w-full font-medium text-gray-900 border-b border-gray-200 focus:border-purple-500 outline-none py-1 bg-transparent"
                >
                  <option value="">Select branch</option>
                  {branches.map((branch) => (
                    <option key={branch.id} value={branch.id}>{branch.name}</option>
                  ))}
                </select>
              ) : (
                <p className="font-medium text-gray-900">
                  {branches.find(b => b.id === member.branch_id)?.name || member.branch_name || 'Not assigned'}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Groups & Subgroups Section */}
      {isEditing && groups.length > 0 && (
        <div className="bg-white rounded-2xl shadow-sm border p-6">
          <div className="flex items-center gap-2 mb-4">
            <UsersIcon className="w-5 h-5 text-gray-600" />
            <h3 className="text-lg font-semibold text-gray-900">Groups & Subgroups</h3>
          </div>
          <div className="space-y-4">
            {groups.map((group) => (
              <div key={group.id} className="border border-gray-200 rounded-xl p-4">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={(formData.group_ids || []).includes(group.id)}
                    onChange={() => handleGroupToggle(group.id)}
                    className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                  />
                  <span className="font-medium text-gray-800">{group.name}</span>
                </label>

                {(formData.group_ids || []).includes(group.id) && group.subgroups && group.subgroups.length > 0 && (
                  <div className="mt-3 ml-7 space-y-2">
                    <p className="text-xs text-gray-500 uppercase font-medium">Subgroups:</p>
                    <div className="grid grid-cols-2 gap-2">
                      {group.subgroups.map((subgroup) => (
                        <label key={subgroup.id} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={(formData.subgroup_ids || []).includes(subgroup.id)}
                            onChange={() => handleSubgroupToggle(subgroup.id)}
                            className="w-3.5 h-3.5 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
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
        </div>
      )}

      {/* Member Since */}
      {member.created_at && (
        <p className="text-sm text-gray-400 text-center mt-6">
          Member since {new Date(member.created_at).toLocaleDateString()}
        </p>
      )}
    </div>
  );
}
