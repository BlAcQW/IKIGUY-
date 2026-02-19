import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Edit, Trash2, Users, ChevronRight, List, Grid, X } from 'lucide-react';
import { getApiUrl } from '../../config/api-config';
import ConfirmDialog from '../../components/ConfirmDialog';
import { CheckCircle } from 'lucide-react';

interface Group {
  id: string;
  name: string;
  description?: string;
  subgroup_count: number;
  is_active: boolean;
  created_at: string;
}

export default function GroupManagement() {
  const navigate = useNavigate();
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list'); // Default to list view
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '' });
  const [editingGroup, setEditingGroup] = useState<Group | null>(null);
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    groupId: string | null;
    groupName: string;
    isLoading: boolean;
  }>({ isOpen: false, groupId: null, groupName: '', isLoading: false });
  const [successDialog, setSuccessDialog] = useState<{
    isOpen: boolean;
    message: string;
    title: string;
  }>({ isOpen: false, message: '', title: '' });

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(getApiUrl('groups'), {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setGroups(data);
      }
    } catch (error) {
      console.error('Error fetching groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch(getApiUrl('groups'), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowCreateModal(false);
        setFormData({ name: '', description: '' });
        setSuccessDialog({
          isOpen: true,
          title: 'Group Created Successfully!',
          message: `"${formData.name}" has been created successfully.`,
        });
        fetchGroups();
      } else {
        const error = await response.json();
        setSuccessDialog({
          isOpen: true,
          title: 'Error Creating Group',
          message: error.detail || 'Failed to create group. Please try again.',
        });
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to create group');
    }
  };

  const openEditModal = (group: Group) => {
    setEditingGroup(group);
    setFormData({ name: group.name, description: group.description || '' });
    setShowEditModal(true);
  };

  const handleUpdateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingGroup) return;

    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch(getApiUrl(`groups/${editingGroup.id}`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setShowEditModal(false);
        setEditingGroup(null);
        setFormData({ name: '', description: '' });
        setSuccessDialog({
          isOpen: true,
          title: 'Group Updated Successfully!',
          message: `"${formData.name}" has been updated successfully.`,
        });
        fetchGroups();
      } else {
        const error = await response.json();
        setSuccessDialog({
          isOpen: true,
          title: 'Error Updating Group',
          message: error.detail || 'Failed to update group. Please try again.',
        });
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to update group');
    }
  };

  const openDeleteDialog = (group: Group) => {
    setDeleteDialog({
      isOpen: true,
      groupId: group.id,
      groupName: group.name,
      isLoading: false
    });
  };

  const handleDeleteGroup = async () => {
    if (!deleteDialog.groupId) return;

    setDeleteDialog(prev => ({ ...prev, isLoading: true }));
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(getApiUrl(`groups/${deleteDialog.groupId}`), {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setSuccessDialog({
          isOpen: true,
          title: 'Group Deleted Successfully!',
          message: `"${deleteDialog.groupName}" has been deleted successfully.`,
        });
        setDeleteDialog({ isOpen: false, groupId: null, groupName: '', isLoading: false });
        fetchGroups();
      } else {
        setSuccessDialog({
          isOpen: true,
          title: 'Error Deleting Group',
          message: 'Failed to delete group. Please try again.',
        });
        setDeleteDialog(prev => ({ ...prev, isLoading: false }));
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to delete group');
      setDeleteDialog(prev => ({ ...prev, isLoading: false }));
    }
  };

  if (loading) {
    return <div className="p-8">Loading groups...</div>;
  }

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Group Management</h1>
          <p className="text-sm text-gray-600 mt-1">Create and manage member groups and subgroups</p>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          {/* View Toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded transition ${
                viewMode === 'list'
                  ? 'bg-white text-purple-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              title="List view"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded transition ${
                viewMode === 'grid'
                  ? 'bg-white text-purple-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              title="Grid view"
            >
              <Grid className="w-4 h-4" />
            </button>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center gap-2 flex-1 sm:flex-initial justify-center"
          >
            <Plus className="w-4 h-4" />
            Create Group
          </button>
        </div>
      </div>

      {/* Groups Display */}
      {groups.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-500">No groups created yet.</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 text-purple-600 hover:underline"
          >
            Create your first group
          </button>
        </div>
      ) : viewMode === 'list' ? (
        // List View
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="divide-y divide-gray-200">
            {groups.map(group => (
              <div key={group.id} className="p-4 sm:p-6 hover:bg-gray-50 transition">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">{group.name}</h3>
                    {group.description && (
                      <p className="text-sm text-gray-600 mt-1">{group.description}</p>
                    )}
                    <div className="flex items-center gap-2 text-sm text-gray-600 mt-2">
                      <Users className="w-4 h-4" />
                      <span>{group.subgroup_count} subgroup{group.subgroup_count !== 1 ? 's' : ''}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 sm:gap-3">
                    <button
                      onClick={() => navigate(`/admin/groups/${group.id}/subgroups`)}
                      className="btn-secondary flex items-center gap-2"
                    >
                      Manage Subgroups
                      <ChevronRight className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => openEditModal(group)}
                      className="btn-icon-sm"
                      title="Edit group"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => openDeleteDialog(group)}
                      className="btn-icon-sm text-red-600 hover:bg-red-50"
                      title="Delete group"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        // Grid View
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {groups.map(group => (
            <div key={group.id} className="bg-white rounded-lg shadow p-6 hover:shadow-md transition">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{group.name}</h3>
                  {group.description && (
                    <p className="text-sm text-gray-600 mt-1">{group.description}</p>
                  )}
                </div>
                <div className="flex gap-2 ml-2">
                  <button
                    onClick={() => openEditModal(group)}
                    className="btn-icon-sm"
                    title="Edit group"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => openDeleteDialog(group)}
                    className="btn-icon-sm text-red-600 hover:bg-red-50"
                    title="Delete group"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2 text-sm text-gray-600 mb-4">
                <Users className="w-4 h-4" />
                <span>{group.subgroup_count} subgroup{group.subgroup_count !== 1 ? 's' : ''}</span>
              </div>

              <button
                onClick={() => navigate(`/admin/groups/${group.id}/subgroups`)}
                className="w-full btn-secondary flex items-center justify-center gap-2"
              >
                Manage Subgroups
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in"
             onClick={() => setShowCreateModal(false)}>
          <div className="min-h-full flex items-end sm:items-center justify-center p-0 sm:p-4">
            <div className="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden transform transition-all duration-200"
                 onClick={(e) => e.stopPropagation()}>
              {/* Header with gradient */}
              <div className="bg-gradient-to-r from-purple-600 via-purple-700 to-blue-700 px-6 py-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center">
                      <Plus className="w-5 h-5 text-white" />
                    </div>
                    <h2 className="text-xl font-bold text-white">Create New Group</h2>
                  </div>
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="p-2 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-all"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <form onSubmit={handleCreateGroup}>
                <div className="p-6 space-y-5">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Group Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                      placeholder="e.g., Age Tribes, Service Units"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Description
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all resize-none"
                      rows={3}
                      placeholder="Optional description of this group"
                    />
                    <p className="mt-1 text-xs text-gray-500">This helps others understand the purpose of this group</p>
                  </div>
                </div>

                <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 px-4 py-2.5 text-gray-700 font-medium border-2 border-gray-300 rounded-lg hover:bg-gray-100 transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all shadow-lg hover:shadow-xl"
                  >
                    Create Group
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editingGroup && (
        <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in"
             onClick={() => setShowEditModal(false)}>
          <div className="min-h-full flex items-end sm:items-center justify-center p-0 sm:p-4">
            <div className="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden transform transition-all duration-200"
                 onClick={(e) => e.stopPropagation()}>
              {/* Header with gradient */}
              <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 px-6 py-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center">
                      <Edit className="w-5 h-5 text-white" />
                    </div>
                    <h2 className="text-xl font-bold text-white">Edit Group</h2>
                  </div>
                  <button
                    onClick={() => setShowEditModal(false)}
                    className="p-2 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-all"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <form onSubmit={handleUpdateGroup}>
                <div className="p-6 space-y-5">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Group Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Description
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none"
                      rows={3}
                    />
                    <p className="mt-1 text-xs text-gray-500">This helps others understand the purpose of this group</p>
                  </div>
                </div>

                <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3">
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="flex-1 px-4 py-2.5 text-gray-700 font-medium border-2 border-gray-300 rounded-lg hover:bg-gray-100 transition-all"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg hover:shadow-xl"
                  >
                    Update Group
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, groupId: null, groupName: '', isLoading: false })}
        onConfirm={handleDeleteGroup}
        title="Delete Group"
        message="Are you sure you want to delete this group? All subgroups will also be deleted."
        itemName={deleteDialog.groupName}
        confirmText="Delete Group"
        cancelText="Keep Group"
        variant="danger"
        isLoading={deleteDialog.isLoading}
      />

      {/* Success Dialog */}
      {successDialog.isOpen && (
        <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden transform transition-all duration-200">
            {/* Success gradient bar */}
            <div className="h-2 bg-gradient-to-r from-green-500 to-emerald-600" />
            
            <div className="p-8">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0 ring-4 ring-green-100/50">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{successDialog.title}</h3>
                  <p className="text-gray-600 mb-6">{successDialog.message}</p>
                  <button
                    onClick={() => setSuccessDialog({ isOpen: false, message: '', title: '' })}
                    className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all shadow-lg hover:shadow-xl"
                  >
                    Got it
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
