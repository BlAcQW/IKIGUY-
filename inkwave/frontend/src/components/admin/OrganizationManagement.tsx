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
import { api } from '../../lib/api';
import toast from 'react-hot-toast';

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
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
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
      const response = await api.organizations.list();
      const data = response.data;

      // Extract organizations from the response structure
      const orgList = data.map((item: any) => ({
        ...item.organization,
        role: item.role,
        joined_at: item.joined_at
      }));

      setOrganizations(orgList);
      if (orgList.length > 0 && !selectedOrg) {
        setSelectedOrg(orgList[0]);
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to load organizations';
      onError?.(errorMsg);
      toast.error(errorMsg);
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadOrgMembers = async (orgId: string) => {
    try {
      const response = await api.organizations.listMembers(orgId);
      setMembers(response.data);
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to load members';
      toast.error(errorMsg);
      console.error('Failed to load members:', error);
      setMembers([]);
    }
  };

  const loadOrgInvitations = async (orgId: string) => {
    try {
      const response = await api.organizations.listInvitations(orgId);
      setInvitations(response.data);
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Failed to load invitations';
      toast.error(errorMsg);
      console.error('Failed to load invitations:', error);
      setInvitations([]);
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
        // Use the configured API client instead of raw fetch
        const response = await api.organizations.create(formData);

        toast.success(`Organization "${formData.display_name}" created successfully!`);

        await loadOrganizations();
        setShowCreateModal(false);
        setFormData({ name: '', display_name: '', description: '', industry: '', website: '' });
      } catch (error: any) {
        // Show detailed error message from backend
        const errorMessage = error.response?.data?.detail ||
                            error.message ||
                            'Failed to create organization';
        toast.error(errorMessage);
        onError?.(errorMessage);
        console.error('Organization creation failed:', error);
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                placeholder="my-organization"
              />
              <p className="text-xs text-gray-600 mt-1">Lowercase, no spaces (used in URLs)</p>
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                placeholder="e.g., Technology, Education, Healthcare"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Website
              </label>
              <input
                type="text"
                value={formData.website}
                onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
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

  const EditOrganizationModal = () => {
    const [formData, setFormData] = useState({
      display_name: selectedOrg?.display_name || '',
      description: selectedOrg?.description || '',
      industry: selectedOrg?.industry || '',
      website: selectedOrg?.website || ''
    });

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!selectedOrg) return;

      try {
        await api.organizations.update(selectedOrg.id, formData);
        toast.success('Organization updated successfully!');
        await loadOrganizations();
        setShowEditModal(false);
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || 'Failed to update organization';
        toast.error(errorMessage);
        onError?.(errorMessage);
        console.error('Organization update failed:', error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Edit Organization</h2>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Display Name *
              </label>
              <input
                type="text"
                required
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                rows={3}
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Website
              </label>
              <input
                type="text"
                value={formData.website}
                onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
              />
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowEditModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const DeleteOrganizationModal = () => {
    const handleDelete = async () => {
      if (!selectedOrg) return;

      try {
        await api.organizations.delete(selectedOrg.id);
        toast.success('Organization deleted successfully!');
        await loadOrganizations();
        setShowDeleteModal(false);
        setSelectedOrg(null);
      } catch (error: any) {
        const errorMessage = error.response?.data?.detail || 'Failed to delete organization';
        toast.error(errorMessage);
        onError?.(errorMessage);
        console.error('Organization deletion failed:', error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Delete Organization</h2>
          </div>
          <div className="p-6">
            <p className="text-gray-600 mb-4">
              Are you sure you want to delete <strong>{selectedOrg?.display_name}</strong>?
              This will deactivate the organization and all its members will lose access.
            </p>
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
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
                  onClick={() => setSelectedOrg(org)}
                  className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                    selectedOrg?.id === org.id ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Building2 className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900 truncate">
                          {org.display_name}
                        </h3>
                        {getRoleIcon(org.role || 'user')}
                      </div>
                      <p className="text-xs text-gray-500 mb-1">{org.industry || 'No industry'}</p>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getRoleBadgeColor(org.role || 'user')}`}>
                          {org.role}
                        </span>
                        {org.is_active ? (
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
                    <div className="flex gap-2">
                      <button
                        onClick={() => setShowEditModal(true)}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Edit organization"
                      >
                        <Edit className="w-5 h-5 text-gray-600" />
                      </button>
                      <button
                        onClick={() => setShowDeleteModal(true)}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        title="Delete organization"
                      >
                        <Trash2 className="w-5 h-5 text-red-600" />
                      </button>
                    </div>
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
      {showEditModal && <EditOrganizationModal />}
      {showDeleteModal && <DeleteOrganizationModal />}
      {showInviteModal && <InviteMemberModal />}
    </div>
  );
}
