/**
 * Organization Management Page
 *
 * Manage organizations, members, and invitations.
 */

import React, { useState, useEffect } from 'react';
import {
  Building2,
  Users,
  Mail,
  Plus,
  Search,
  MoreVertical,
  Edit,
  Trash2,
  UserPlus,
  Crown,
  Shield,
  User as UserIcon,
  CheckCircle,
  XCircle,
  Clock,
  ExternalLink
} from 'lucide-react';

interface Organization {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  industry?: string;
  website?: string;
  is_active: boolean;
  created_at: string;
  member_count?: number;
  role?: 'owner' | 'admin' | 'user';
}

interface OrganizationMember {
  user_id: string;
  user_email: string;
  user_name?: string;
  role: 'owner' | 'admin' | 'user';
  joined_at: string;
  is_active: boolean;
}

interface OrganizationInvitation {
  id: string;
  email: string;
  role: 'admin' | 'user';
  status: 'pending' | 'accepted' | 'expired';
  invited_at: string;
  invited_by: string;
}

interface OrganizationManagementProps {
  apiBaseUrl: string;
  onError?: (error: string) => void;
}

export default function OrganizationManagement({
  apiBaseUrl,
  onError
}: OrganizationManagementProps) {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [invitations, setInvitations] = useState<OrganizationInvitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'members' | 'invitations'>('overview');

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrg) {
      loadOrgMembers(selectedOrg.id);
      loadOrgInvitations(selectedOrg.id);
    }
  }, [selectedOrg]);

  const loadOrganizations = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${apiBaseUrl}/api/v1/organizations`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to load organizations');

      const data = await response.json();
      setOrganizations(data);
      if (data.length > 0 && !selectedOrg) {
        setSelectedOrg(data[0].organization);
      }
    } catch (error) {
      onError?.('Failed to load organizations');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadOrgMembers = async (orgId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${apiBaseUrl}/api/v1/organizations/${orgId}/users`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        // Map the OrganizationUser objects to the expected member format
        const mappedMembers = data.map((user: any) => ({
          user_id: user.user_id,
          user_email: user.email,
          user_name: user.display_name || user.email.split('@')[0],
          role: user.role,
          joined_at: user.joined_at,
          is_active: user.is_active
        }));
        setMembers(mappedMembers);
      }
    } catch (error) {
      console.error('Failed to load members:', error);
    }
  };

  const loadOrgInvitations = async (orgId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${apiBaseUrl}/api/v1/organizations/${orgId}/invitations`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setInvitations(data);
      }
    } catch (error) {
      console.error('Failed to load invitations:', error);
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner':
        return <Crown className="w-4 h-4 text-yellow-500" />;
      case 'admin':
        return <Shield className="w-4 h-4 text-blue-500" />;
      default:
        return <UserIcon className="w-4 h-4 text-gray-500" />;
    }
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner':
        return 'bg-yellow-100 text-yellow-800';
      case 'admin':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const CreateOrganizationModal = () => {
    const [formData, setFormData] = useState({
      name: '',
      display_name: '',
      description: '',
      industry: '',
      website: ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${apiBaseUrl}/api/v1/organizations`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(formData)
        });

        if (!response.ok) throw new Error('Failed to create organization');

        await loadOrganizations();
        setShowCreateModal(false);
        setFormData({ name: '', display_name: '', description: '', industry: '', website: '' });
      } catch (error) {
        onError?.('Failed to create organization');
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Create Organization</h2>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Organization Name *
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="my-organization"
              />
              <p className="text-xs text-gray-500 mt-1">Lowercase, no spaces (used in URLs)</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Display Name *
              </label>
              <input
                type="text"
                required
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="My Organization"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                placeholder="Brief description of your organization"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Industry
              </label>
              <input
                type="text"
                value={formData.industry}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Technology, Education, Healthcare"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Website
              </label>
              <input
                type="url"
                value={formData.website}
                onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="https://example.com"
              />
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const InviteMemberModal = () => {
    const [email, setEmail] = useState('');
    const [role, setRole] = useState<'admin' | 'user'>('user');

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!selectedOrg) return;

      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${apiBaseUrl}/api/v1/organizations/${selectedOrg.id}/invitations`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ email, role })
        });

        if (!response.ok) throw new Error('Failed to send invitation');

        await loadOrgInvitations(selectedOrg.id);
        setShowInviteModal(false);
        setEmail('');
        setRole('user');
      } catch (error) {
        onError?.('Failed to send invitation');
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Invite Member</h2>
            <p className="text-sm text-gray-600 mt-1">
              Send an invitation to join {selectedOrg?.display_name}
            </p>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address *
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="user@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Role *
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as 'admin' | 'user')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="user">User - Basic access</option>
                <option value="admin">Admin - Full access</option>
              </select>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowInviteModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Send Invitation
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading organizations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Organizations</h1>
          <p className="text-gray-600 mt-1">Manage your organizations and members</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Create Organization
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Organizations List */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search organizations..."
                  className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
              {organizations.map((org) => (
                <button
                  key={org.id}
                  onClick={() => setSelectedOrg(org.organization)}
                  className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                    selectedOrg?.id === org.organization.id ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Building2 className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900 truncate">
                          {org.organization.display_name}
                        </h3>
                        {getRoleIcon(org.role)}
                      </div>
                      <p className="text-xs text-gray-500 mb-1">{org.organization.industry || 'No industry'}</p>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getRoleBadgeColor(org.role)}`}>
                          {org.role}
                        </span>
                        {org.organization.is_active ? (
                          <CheckCircle className="w-3 h-3 text-green-500" />
                        ) : (
                          <XCircle className="w-3 h-3 text-red-500" />
                        )}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Organization Details */}
        <div className="lg:col-span-2">
          {selectedOrg ? (
            <div className="space-y-6">
              {/* Organization Info Card */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-6">
                    <div className="flex items-start gap-4">
                      <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                        <Building2 className="w-8 h-8 text-white" />
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold text-gray-900">{selectedOrg.display_name}</h2>
                        <p className="text-gray-600 mt-1">{selectedOrg.description || 'No description'}</p>
                        <div className="flex items-center gap-4 mt-3">
                          <span className="text-sm text-gray-500">
                            <strong>ID:</strong> {selectedOrg.name}
                          </span>
                          {selectedOrg.website && (
                            <a
                              href={selectedOrg.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                            >
                              <ExternalLink className="w-4 h-4" />
                              Website
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                      <MoreVertical className="w-5 h-5 text-gray-600" />
                    </button>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <Users className="w-5 h-5 text-blue-600 mb-2" />
                      <p className="text-2xl font-bold text-gray-900">{members.length}</p>
                      <p className="text-sm text-gray-600">Members</p>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg">
                      <Mail className="w-5 h-5 text-green-600 mb-2" />
                      <p className="text-2xl font-bold text-gray-900">{invitations.filter(i => i.status === 'pending').length}</p>
                      <p className="text-sm text-gray-600">Pending Invites</p>
                    </div>
                    <div className="p-4 bg-purple-50 rounded-lg">
                      <Clock className="w-5 h-5 text-purple-600 mb-2" />
                      <p className="text-2xl font-bold text-gray-900">
                        {new Date(selectedOrg.created_at).toLocaleDateString()}
                      </p>
                      <p className="text-sm text-gray-600">Created</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200">
                <div className="border-b border-gray-200">
                  <div className="flex">
                    <button
                      onClick={() => setActiveTab('overview')}
                      className={`px-6 py-3 font-medium transition-colors ${
                        activeTab === 'overview'
                          ? 'text-blue-600 border-b-2 border-blue-600'
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      Overview
                    </button>
                    <button
                      onClick={() => setActiveTab('members')}
                      className={`px-6 py-3 font-medium transition-colors ${
                        activeTab === 'members'
                          ? 'text-blue-600 border-b-2 border-blue-600'
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      Members ({members.length})
                    </button>
                    <button
                      onClick={() => setActiveTab('invitations')}
                      className={`px-6 py-3 font-medium transition-colors ${
                        activeTab === 'invitations'
                          ? 'text-blue-600 border-b-2 border-blue-600'
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      Invitations ({invitations.length})
                    </button>
                  </div>
                </div>

                <div className="p-6">
                  {activeTab === 'overview' && (
                    <div className="space-y-4">
                      <h3 className="font-semibold text-gray-900">Organization Details</h3>
                      <dl className="grid grid-cols-2 gap-4">
                        <div>
                          <dt className="text-sm text-gray-600">Industry</dt>
                          <dd className="text-sm font-medium text-gray-900">{selectedOrg.industry || 'Not specified'}</dd>
                        </div>
                        <div>
                          <dt className="text-sm text-gray-600">Status</dt>
                          <dd>
                            {selectedOrg.is_active ? (
                              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">Active</span>
                            ) : (
                              <span className="px-2 py-1 bg-red-100 text-red-800 text-xs font-medium rounded">Inactive</span>
                            )}
                          </dd>
                        </div>
                      </dl>
                    </div>
                  )}

                  {activeTab === 'members' && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900">Members</h3>
                        <button
                          onClick={() => setShowInviteModal(true)}
                          className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          <UserPlus className="w-4 h-4" />
                          Invite Member
                        </button>
                      </div>
                      <div className="space-y-2">
                        {members.map((member) => (
                          <div key={member.user_id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                                <span className="text-white font-semibold">
                                  {member.user_email.charAt(0).toUpperCase()}
                                </span>
                              </div>
                              <div>
                                <p className="font-medium text-gray-900">{member.user_name || member.user_email}</p>
                                <p className="text-sm text-gray-600">{member.user_email}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getRoleBadgeColor(member.role)}`}>
                                {member.role}
                              </span>
                              {member.role !== 'owner' && (
                                <button className="p-1 hover:bg-gray-100 rounded transition-colors">
                                  <MoreVertical className="w-4 h-4 text-gray-600" />
                                </button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {activeTab === 'invitations' && (
                    <div className="space-y-4">
                      <h3 className="font-semibold text-gray-900">Invitations</h3>
                      <div className="space-y-2">
                        {invitations.length === 0 ? (
                          <p className="text-center text-gray-500 py-8">No invitations sent</p>
                        ) : (
                          invitations.map((invitation) => (
                            <div key={invitation.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                              <div className="flex items-center gap-3">
                                <Mail className="w-5 h-5 text-gray-400" />
                                <div>
                                  <p className="font-medium text-gray-900">{invitation.email}</p>
                                  <p className="text-sm text-gray-600">
                                    Invited {new Date(invitation.invited_at).toLocaleDateString()}
                                  </p>
                                </div>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className={`px-2 py-1 rounded text-xs font-medium ${getRoleBadgeColor(invitation.role)}`}>
                                  {invitation.role}
                                </span>
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  invitation.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                                  invitation.status === 'accepted' ? 'bg-green-100 text-green-800' :
                                  'bg-gray-100 text-gray-800'
                                }`}>
                                  {invitation.status}
                                </span>
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <Building2 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Organization Selected</h3>
              <p className="text-gray-600">Select an organization from the list to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {showCreateModal && <CreateOrganizationModal />}
      {showInviteModal && <InviteMemberModal />}
    </div>
  );
}
