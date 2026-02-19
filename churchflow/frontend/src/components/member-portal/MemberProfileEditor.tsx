/**
 * Member Profile Editor Component
 *
 * Allows members to edit their own profile information.
 */

import React, { useState } from 'react';
import { Save, User, Phone, Mail, MapPin, Briefcase, Heart, AlertCircle, Users as UsersIcon } from 'lucide-react';
import { useMyProfile, useUpdateMyProfile, UpdateProfileRequest } from '../../hooks/useMemberPortal';
import { getApiUrl } from '../../config/api-config';

interface GroupMembership {
  group_id: string;
  group_name: string;
  selection_mode: 'single' | 'multi';
  subgroups: Array<{
    subgroup_id: string;
    subgroup_name: string;
  }>;
}

export default function MemberProfileEditor() {
  const token = localStorage.getItem('access_token');
  const { data: profile, isLoading, error } = useMyProfile(token);
  const updateMutation = useUpdateMyProfile(token);

  const [formData, setFormData] = useState<UpdateProfileRequest>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [groupMemberships, setGroupMemberships] = useState<GroupMembership[]>([]);
  const [loadingGroups, setLoadingGroups] = useState(true);

  // Update form data when profile loads
  React.useEffect(() => {
    if (profile) {
      setFormData({
        full_name: profile.full_name || profile.name || '',
        email: profile.email || '',
        phone: profile.phone || '',
        date_of_birth: profile.date_of_birth || '',
        gender: profile.gender || '',
        address: profile.address || '',
        city: profile.city || '',
        state: profile.state || '',
        country: profile.country || '',
        occupation: profile.occupation || '',
        employer: profile.employer || '',
        marital_status: profile.marital_status || '',
        spouse_name: profile.spouse_name || '',
        emergency_contact_name: profile.emergency_contact_name || '',
        emergency_contact_phone: profile.emergency_contact_phone || '',
        bio: profile.bio || '',
      });

      // Fetch group memberships
      fetchGroupMemberships();
    }
  }, [profile]);

  const fetchGroupMemberships = async () => {
    if (!profile?.id && !profile?._id) return;

    setLoadingGroups(true);
    try {
      const userId = profile.id || profile._id;
      const response = await fetch(getApiUrl(`members/${userId}/subgroups`), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();

        // Group subgroups by parent group
        const grouped: { [key: string]: GroupMembership } = {};

        data.forEach((item: any) => {
          const groupId = item.group_id;
          if (!grouped[groupId]) {
            grouped[groupId] = {
              group_id: groupId,
              group_name: item.group_name,
              selection_mode: item.selection_mode,
              subgroups: []
            };
          }
          grouped[groupId].subgroups.push({
            subgroup_id: item.subgroup_id,
            subgroup_name: item.subgroup_name
          });
        });

        setGroupMemberships(Object.values(grouped));
      }
    } catch (err) {
      console.error('Failed to fetch group memberships:', err);
    } finally {
      setLoadingGroups(false);
    }
  };

  const handleChange = (field: keyof UpdateProfileRequest, value: string) => {
    setFormData({ ...formData, [field]: value });
    setHasChanges(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateMutation.mutateAsync(formData);
      setHasChanges(false);
      alert('Profile updated successfully!');
    } catch (err) {
      alert('Failed to update profile. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-2 text-red-800">
          <AlertCircle className="h-5 w-5" />
          <span>Failed to load profile. Please try again.</span>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Personal Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <User className="h-5 w-5 text-purple-600" />
          <h2 className="text-xl font-semibold">Personal Information</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name *
            </label>
            <input
              type="text"
              value={formData.full_name || ''}
              onChange={(e) => handleChange('full_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date of Birth
            </label>
            <input
              type="date"
              value={formData.date_of_birth?.split('T')[0] || ''}
              onChange={(e) => handleChange('date_of_birth', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Gender
            </label>
            <select
              value={formData.gender || ''}
              onChange={(e) => handleChange('gender', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
              Marital Status
            </label>
            <select
              value={formData.marital_status || ''}
              onChange={(e) => handleChange('marital_status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="">Select status</option>
              <option value="single">Single</option>
              <option value="married">Married</option>
              <option value="divorced">Divorced</option>
              <option value="widowed">Widowed</option>
            </select>
          </div>

          {formData.marital_status === 'married' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Spouse Name
              </label>
              <input
                type="text"
                value={formData.spouse_name || ''}
                onChange={(e) => handleChange('spouse_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          )}
        </div>

        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Bio
          </label>
          <textarea
            value={formData.bio || ''}
            onChange={(e) => handleChange('bio', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            placeholder="Tell us a little about yourself..."
          />
        </div>
      </div>

      {/* Contact Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Phone className="h-5 w-5 text-purple-600" />
          <h2 className="text-xl font-semibold">Contact Information</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              value={formData.email || ''}
              onChange={(e) => handleChange('email', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Phone
            </label>
            <input
              type="tel"
              value={formData.phone || ''}
              onChange={(e) => handleChange('phone', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Address */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <MapPin className="h-5 w-5 text-purple-600" />
          <h2 className="text-xl font-semibold">Address</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Street Address
            </label>
            <input
              type="text"
              value={formData.address || ''}
              onChange={(e) => handleChange('address', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              City
            </label>
            <input
              type="text"
              value={formData.city || ''}
              onChange={(e) => handleChange('city', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              State/Province
            </label>
            <input
              type="text"
              value={formData.state || ''}
              onChange={(e) => handleChange('state', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Country
            </label>
            <input
              type="text"
              value={formData.country || ''}
              onChange={(e) => handleChange('country', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Professional Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Briefcase className="h-5 w-5 text-purple-600" />
          <h2 className="text-xl font-semibold">Professional Information</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Occupation
            </label>
            <input
              type="text"
              value={formData.occupation || ''}
              onChange={(e) => handleChange('occupation', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Employer
            </label>
            <input
              type="text"
              value={formData.employer || ''}
              onChange={(e) => handleChange('employer', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Emergency Contact */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Heart className="h-5 w-5 text-purple-600" />
          <h2 className="text-xl font-semibold">Emergency Contact</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Emergency Contact Name
            </label>
            <input
              type="text"
              value={formData.emergency_contact_name || ''}
              onChange={(e) => handleChange('emergency_contact_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Emergency Contact Phone
            </label>
            <input
              type="tel"
              value={formData.emergency_contact_phone || ''}
              onChange={(e) => handleChange('emergency_contact_phone', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Group Memberships - Read Only */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <UsersIcon className="h-5 w-5 text-purple-600" />
          <h2 className="text-xl font-semibold">Group Memberships</h2>
        </div>

        {loadingGroups ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          </div>
        ) : groupMemberships.length === 0 ? (
          <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg">
            <p>You are not currently assigned to any groups.</p>
            <p className="text-sm mt-2">Group assignments are managed by administrators.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {groupMemberships.map((group) => (
              <div key={group.group_id} className="border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">{group.group_name}</h3>

                {/* Single-select: show as text */}
                {group.selection_mode === 'single' && group.subgroups.length > 0 && (
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600">Subgroup:</span>
                    <span className="text-sm font-medium text-gray-900">
                      {group.subgroups[0].subgroup_name}
                    </span>
                  </div>
                )}

                {/* Multi-select: show as badges */}
                {group.selection_mode === 'multi' && (
                  <div>
                    <span className="text-sm text-gray-600 block mb-2">Subgroups:</span>
                    <div className="flex flex-wrap gap-2">
                      {group.subgroups.map((subgroup) => (
                        <span
                          key={subgroup.subgroup_id}
                          className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800"
                        >
                          {subgroup.subgroup_name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}

            <div className="text-sm text-gray-500 italic mt-4">
              Group assignments are managed by administrators. Contact your church admin if you need any changes.
            </div>
          </div>
        )}
      </div>

      {/* Save Button */}
      <div className="flex items-center justify-end space-x-4">
        {hasChanges && (
          <span className="text-sm text-gray-600">You have unsaved changes</span>
        )}
        <button
          type="submit"
          disabled={!hasChanges || updateMutation.isPending}
          className="flex items-center space-x-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          <Save className="h-5 w-5" />
          <span>{updateMutation.isPending ? 'Saving...' : 'Save Changes'}</span>
        </button>
      </div>
    </form>
  );
}
