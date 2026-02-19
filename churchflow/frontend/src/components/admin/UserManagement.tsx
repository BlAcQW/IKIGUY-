/**
 * User Management Page
 *
 * Manage users within an organization - view, edit roles, and remove users.
 */

import React, { useState, useEffect } from 'react';
import {
  Users,
  Search,
  Filter,
  MoreVertical,
  Edit,
  Trash2,
  Mail,
  Shield,
  User as UserIcon,
  Crown,
  CheckCircle,
  XCircle,
  UserPlus
} from 'lucide-react';
import ConfirmDialog from '../ConfirmDialog';
import { ResponsiveTable } from '../common';
import { encodeHeaderValue } from '../../lib/header-utils';

interface User {
  id: string;
  email: string;
  name?: string;
  role: 'owner' | 'admin' | 'user';
  is_active: boolean;
  joined_at: string;
  last_login?: string;
}

interface UserManagementProps {
  organizationId: string;
  apiBaseUrl: string;
  currentRole?: string | null;
  isUniversalAdmin?: boolean;
  onError?: (error: string) => void;
  onSuccess?: (message: string) => void;
}

export default function UserManagement({
  organizationId,
  apiBaseUrl,
  currentRole,
  isUniversalAdmin = false,
  onError,
  onSuccess
}: UserManagementProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  // Remove confirmation dialog state
  const [removeDialog, setRemoveDialog] = useState<{
    isOpen: boolean;
    userId: string | null;
    userName: string;
    isLoading: boolean;
  }>({ isOpen: false, userId: null, userName: '', isLoading: false });

  useEffect(() => {
    loadUsers();
  }, [organizationId]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${apiBaseUrl}/api/v1/organizations/${organizationId}/members`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Organization-ID': encodeHeaderValue(organizationId) || ''
          }
        }
      );

      if (!response.ok) throw new Error('Failed to load users');

      const data = await response.json();
      setUsers(data);
    } catch (error) {
      onError?.('Failed to load users');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRole = async (userId: string, newRole: 'admin' | 'user') => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${apiBaseUrl}/api/v1/organizations/${organizationId}/members/${userId}`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'X-Organization-ID': encodeHeaderValue(organizationId) || ''
          },
          body: JSON.stringify({ role: newRole })
        }
      );

      if (!response.ok) throw new Error('Failed to update user role');

      await loadUsers();
      onSuccess?.('User role updated successfully');
      setShowEditModal(false);
    } catch (error) {
      onError?.('Failed to update user role');
    }
  };

  // Open remove confirmation dialog
  const openRemoveDialog = (user: User) => {
    setRemoveDialog({
      isOpen: true,
      userId: user.id,
      userName: user.name || user.email,
      isLoading: false,
    });
  };

  // Handle confirmed remove
  const handleRemoveUser = async () => {
    if (!removeDialog.userId) return;

    setRemoveDialog(prev => ({ ...prev, isLoading: true }));

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${apiBaseUrl}/api/v1/organizations/${organizationId}/members/${removeDialog.userId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
            'X-Organization-ID': encodeHeaderValue(organizationId) || ''
          }
        }
      );

      if (!response.ok) throw new Error('Failed to remove user');

      setRemoveDialog({ isOpen: false, userId: null, userName: '', isLoading: false });
      await loadUsers();
      onSuccess?.('User removed from organization');
    } catch (error) {
      setRemoveDialog(prev => ({ ...prev, isLoading: false }));
      onError?.('Failed to remove user');
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

  const filteredUsers = users.filter(user => {
    const matchesSearch =
      user.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesRole = roleFilter === 'all' || user.role === roleFilter;

    return matchesSearch && matchesRole;
  });

  const EditUserModal = () => {
    if (!selectedUser) return null;

    const [role, setRole] = useState(selectedUser.role);

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Edit User</h2>
            <p className="text-sm text-gray-600 mt-1">Update user role and permissions</p>
          </div>
          <div className="p-6 space-y-4">
            <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-white font-semibold">
                  {selectedUser.email.charAt(0).toUpperCase()}
                </span>
              </div>
              <div>
                <p className="font-medium text-gray-900">{selectedUser.name || selectedUser.email}</p>
                <p className="text-sm text-gray-600">{selectedUser.email}</p>
              </div>
            </div>

            {selectedUser.role !== 'owner' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Role
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
            )}

            {selectedUser.role === 'owner' && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-900">
                  <strong>Note:</strong> Organization owners cannot have their role changed.
                </p>
              </div>
            )}

            <div className="flex gap-3 pt-4">
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setSelectedUser(null);
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              {selectedUser.role !== 'owner' && (
                <button
                  onClick={() => handleUpdateRole(selectedUser.id, role as 'admin' | 'user')}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Save Changes
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading users...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
          <p className="text-gray-600 mt-1">Manage users and their roles</p>
        </div>
        <a
          href="/admin/organizations"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <UserPlus className="w-5 h-5" />
          Invite User
        </a>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{users.length}</p>
          </div>
          <p className="text-sm text-gray-600">Total Users</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
              <Crown className="w-5 h-5 text-yellow-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {users.filter(u => u.role === 'owner').length}
            </p>
          </div>
          <p className="text-sm text-gray-600">Owners</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {users.filter(u => u.role === 'admin').length}
            </p>
          </div>
          <p className="text-sm text-gray-600">Admins</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {users.filter(u => u.is_active).length}
            </p>
          </div>
          <p className="text-sm text-gray-600">Active Users</p>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        {/* Table Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search users by name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Roles</option>
                <option value="owner">Owners</option>
                <option value="admin">Admins</option>
                <option value="user">Users</option>
              </select>
            </div>
          </div>
        </div>

        {/* Table Content */}
        <ResponsiveTable
          columns={[
            {
              key: 'email',
              label: 'User',
              render: (value, user) => (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <span className="text-white font-semibold">
                      {user.email.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{user.name || 'No name'}</p>
                    <p className="text-sm text-gray-600">{user.email}</p>
                  </div>
                </div>
              ),
            },
            {
              key: 'role',
              label: 'Role',
              render: (value, user) => (
                <div className="flex items-center gap-2">
                  {getRoleIcon(user.role)}
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getRoleBadgeColor(user.role)}`}>
                    {user.role}
                  </span>
                </div>
              ),
            },
            {
              key: 'is_active',
              label: 'Status',
              render: (value, user) =>
                user.is_active ? (
                  <div className="flex items-center gap-2 text-green-600">
                    <CheckCircle className="w-4 h-4" />
                    <span className="text-sm font-medium">Active</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-red-600">
                    <XCircle className="w-4 h-4" />
                    <span className="text-sm font-medium">Inactive</span>
                  </div>
                ),
            },
            {
              key: 'joined_at',
              label: 'Joined',
              render: (value) => new Date(value).toLocaleDateString(),
            },
            {
              key: 'last_login',
              label: 'Last Login',
              render: (value) => (value ? new Date(value).toLocaleDateString() : 'Never'),
            },
            {
              key: 'id',
              label: 'Actions',
              render: (value, user) => (
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => {
                      setSelectedUser(user);
                      setShowEditModal(true);
                    }}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="Edit user"
                  >
                    <Edit className="w-4 h-4 text-gray-600" />
                  </button>
                  {user.role !== 'owner' && (currentRole === 'admin' || isUniversalAdmin) && (
                    <button
                      onClick={() => openRemoveDialog(user)}
                      className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                      title="Remove user"
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </button>
                  )}
                </div>
              ),
            },
          ]}
          data={filteredUsers}
          keyField="id"
          emptyMessage={
            <div className="text-center py-12">
              <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No users found</p>
              <p className="text-sm text-gray-500 mt-1">Try adjusting your search or filters</p>
            </div>
          }
        />
      </div>

      {/* Edit User Modal */}
      {showEditModal && <EditUserModal />}

      {/* Remove Confirmation Dialog */}
      <ConfirmDialog
        isOpen={removeDialog.isOpen}
        onClose={() => setRemoveDialog({ isOpen: false, userId: null, userName: '', isLoading: false })}
        onConfirm={handleRemoveUser}
        title="Remove User"
        message="Are you sure you want to remove this user from the organization? They will lose access to all organization resources."
        itemName={removeDialog.userName}
        confirmText="Remove User"
        cancelText="Keep User"
        variant="danger"
        isLoading={removeDialog.isLoading}
      />
    </div>
  );
}
