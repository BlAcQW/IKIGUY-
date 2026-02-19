import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Edit, Trash2, Users, ChevronLeft, Eye, UserPlus } from 'lucide-react';
import { getApiUrl } from '../../config/api-config';
import ConfirmDialog from '../../components/ConfirmDialog';
import MemberAssignmentModal from '../../components/groups/MemberAssignmentModal';

interface Group {
  id: string;
  name: string;
  description?: string;
}

interface Subgroup {
  id: string;
  group_id: string;
  name: string;
  description?: string;
  selection_mode: 'single' | 'multi';
  member_count: number;
  is_active: boolean;
  created_at: string;
}

interface SubgroupMember {
  user_id: string;
  full_name: string;
  email: string;
  phone_number?: string;
  joined_at: string;
}

export default function SubgroupManagement() {
  const navigate = useNavigate();
  const { groupId } = useParams<{ groupId: string }>();
  const [group, setGroup] = useState<Group | null>(null);
  const [subgroups, setSubgroups] = useState<Subgroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showMembersModal, setShowMembersModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    selection_mode: 'multi' as 'single' | 'multi'
  });
  const [editingSubgroup, setEditingSubgroup] = useState<Subgroup | null>(null);
  const [viewingMembers, setViewingMembers] = useState<SubgroupMember[]>([]);
  const [viewingSubgroupName, setViewingSubgroupName] = useState('');
  const [showAssignmentModal, setShowAssignmentModal] = useState(false);
  const [assignmentSubgroup, setAssignmentSubgroup] = useState<Subgroup | null>(null);
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    subgroupId: string | null;
    subgroupName: string;
    isLoading: boolean;
  }>({ isOpen: false, subgroupId: null, subgroupName: '', isLoading: false });

  useEffect(() => {
    if (groupId) {
      fetchGroupAndSubgroups();
    }
  }, [groupId]);

  const fetchGroupAndSubgroups = async () => {
    try {
      const token = localStorage.getItem('access_token');

      // Fetch group details
      const groupResponse = await fetch(getApiUrl(`groups/${groupId}`), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (groupResponse.ok) {
        const groupData = await groupResponse.json();
        setGroup({
          id: groupData.id,
          name: groupData.name,
          description: groupData.description
        });

        // Subgroups are included in the group response
        if (groupData.subgroups) {
          setSubgroups(groupData.subgroups);
        }
      }
    } catch (error) {
      console.error('Error fetching group and subgroups:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubgroup = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch(getApiUrl(`groups/${groupId}/subgroups`), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        alert('Subgroup created successfully!');
        setShowCreateModal(false);
        setFormData({ name: '', description: '', selection_mode: 'multi' });
        fetchGroupAndSubgroups();
      } else {
        const error = await response.json();
        alert(`Failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to create subgroup');
    }
  };

  const openEditModal = (subgroup: Subgroup) => {
    setEditingSubgroup(subgroup);
    setFormData({
      name: subgroup.name,
      description: subgroup.description || '',
      selection_mode: subgroup.selection_mode
    });
    setShowEditModal(true);
  };

  const handleUpdateSubgroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingSubgroup) return;

    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch(getApiUrl(`subgroups/${editingSubgroup.id}`), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description
        })
      });

      if (response.ok) {
        alert('Subgroup updated successfully!');
        setShowEditModal(false);
        setEditingSubgroup(null);
        setFormData({ name: '', description: '', selection_mode: 'multi' });
        fetchGroupAndSubgroups();
      } else {
        const error = await response.json();
        alert(`Failed: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to update subgroup');
    }
  };

  const openDeleteDialog = (subgroup: Subgroup) => {
    setDeleteDialog({
      isOpen: true,
      subgroupId: subgroup.id,
      subgroupName: subgroup.name,
      isLoading: false
    });
  };

  const handleDeleteSubgroup = async () => {
    if (!deleteDialog.subgroupId) return;

    setDeleteDialog(prev => ({ ...prev, isLoading: true }));
    const token = localStorage.getItem('access_token');

    try {
      const response = await fetch(getApiUrl(`subgroups/${deleteDialog.subgroupId}`), {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        alert('Subgroup deleted successfully!');
        setDeleteDialog({ isOpen: false, subgroupId: null, subgroupName: '', isLoading: false });
        fetchGroupAndSubgroups();
      } else {
        alert('Failed to delete subgroup');
        setDeleteDialog(prev => ({ ...prev, isLoading: false }));
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to delete subgroup');
      setDeleteDialog(prev => ({ ...prev, isLoading: false }));
    }
  };

  const handleViewMembers = async (subgroup: Subgroup) => {
    const token = localStorage.getItem('access_token');
    try {
      const response = await fetch(getApiUrl(`subgroups/${subgroup.id}/members`), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const members = await response.json();
        setViewingMembers(members);
        setViewingSubgroupName(subgroup.name);
        setShowMembersModal(true);
      } else {
        alert('Failed to fetch members');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to fetch members');
    }
  };

  const handleAssignMembers = (subgroup: Subgroup) => {
    setAssignmentSubgroup(subgroup);
    setShowAssignmentModal(true);
  };

  const handleMemberAssigned = () => {
    // Refresh subgroups to update member counts
    fetchGroupAndSubgroups();
  };

  if (loading) {
    return <div className="p-8">Loading subgroups...</div>;
  }

  if (!group) {
    return <div className="p-8">Group not found</div>;
  }

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto">
      {/* Header with Breadcrumb */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/admin/groups')}
          className="flex items-center text-purple-600 hover:text-purple-700 mb-4"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Groups
        </button>

        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="text-sm text-gray-500 mb-1">
              Groups &gt; {group.name}
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Subgroup Management</h1>
            {group.description && (
              <p className="text-sm text-gray-600 mt-1">{group.description}</p>
            )}
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary flex items-center gap-2 w-full sm:w-auto justify-center"
          >
            <Plus className="w-4 h-4" />
            Create Subgroup
          </button>
        </div>
      </div>

      {/* Subgroups Table */}
      {subgroups.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-500">No subgroups created yet.</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-4 text-purple-600 hover:underline"
          >
            Create your first subgroup
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Selection Mode
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Members
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {subgroups.map((subgroup) => (
                  <tr key={subgroup.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {subgroup.name}
                        </div>
                        {subgroup.description && (
                          <div className="text-sm text-gray-500">
                            {subgroup.description}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {subgroup.selection_mode === 'single' ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          Single-select
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Multi-select
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {subgroup.member_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => handleViewMembers(subgroup)}
                          className="btn-icon-sm"
                          title="View members"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleAssignMembers(subgroup)}
                          className="btn-icon-sm text-green-600 hover:bg-green-50"
                          title="Assign members"
                        >
                          <UserPlus className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => openEditModal(subgroup)}
                          className="btn-icon-sm"
                          title="Edit subgroup"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => openDeleteDialog(subgroup)}
                          className="btn-icon-sm text-red-600 hover:bg-red-50"
                          title="Delete subgroup"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in"
             onClick={() => setShowCreateModal(false)}>
          <div className="min-h-full flex items-end sm:items-center justify-center p-0 sm:p-4">
            <div className="modal-content w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl animate-modal-enter"
                 onClick={(e) => e.stopPropagation()}>
              <div className="modal-header px-4 sm:px-6 py-4">
                <h2 className="text-lg font-semibold">Create New Subgroup</h2>
              </div>

              <form onSubmit={handleCreateSubgroup}>
                <div className="modal-body space-y-4 px-4 sm:px-6">
                  <div>
                    <label className="label">
                      Subgroup Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input"
                      placeholder="e.g., January Born, Choir"
                      required
                    />
                  </div>

                  <div>
                    <label className="label">Description</label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="input"
                      rows={3}
                      placeholder="Optional description of this subgroup"
                    />
                  </div>

                  <div>
                    <label className="label">
                      Selection Mode <span className="text-red-500">*</span>
                    </label>
                    <div className="space-y-2 mt-2">
                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="radio"
                          name="selection_mode"
                          value="multi"
                          checked={formData.selection_mode === 'multi'}
                          onChange={(e) => setFormData({ ...formData, selection_mode: e.target.value as 'multi' })}
                          className="mt-1"
                        />
                        <div>
                          <div className="font-medium text-gray-900">Multi-select</div>
                          <div className="text-sm text-gray-600">
                            Members can belong to multiple subgroups (e.g., Choir, Prayer, Ushering)
                          </div>
                        </div>
                      </label>
                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="radio"
                          name="selection_mode"
                          value="single"
                          checked={formData.selection_mode === 'single'}
                          onChange={(e) => setFormData({ ...formData, selection_mode: e.target.value as 'single' })}
                          className="mt-1"
                        />
                        <div>
                          <div className="font-medium text-gray-900">Single-select</div>
                          <div className="text-sm text-gray-600">
                            Members can only be in ONE subgroup (e.g., January Born OR February Born)
                          </div>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>

                <div className="modal-footer px-4 sm:px-6 py-4 flex gap-3">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary flex-1">
                    Create Subgroup
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && editingSubgroup && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in"
             onClick={() => setShowEditModal(false)}>
          <div className="min-h-full flex items-end sm:items-center justify-center p-0 sm:p-4">
            <div className="modal-content w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl animate-modal-enter"
                 onClick={(e) => e.stopPropagation()}>
              <div className="modal-header px-4 sm:px-6 py-4">
                <h2 className="text-lg font-semibold">Edit Subgroup</h2>
              </div>

              <form onSubmit={handleUpdateSubgroup}>
                <div className="modal-body space-y-4 px-4 sm:px-6">
                  <div>
                    <label className="label">
                      Subgroup Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input"
                      required
                    />
                  </div>

                  <div>
                    <label className="label">Description</label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      className="input"
                      rows={3}
                    />
                  </div>

                  <div className="bg-gray-50 p-3 rounded-md">
                    <div className="text-sm text-gray-600">
                      <strong>Selection Mode:</strong>{' '}
                      {editingSubgroup.selection_mode === 'single' ? 'Single-select' : 'Multi-select'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      Selection mode cannot be changed after creation
                    </div>
                  </div>
                </div>

                <div className="modal-footer px-4 sm:px-6 py-4 flex gap-3">
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="btn-secondary flex-1"
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn-primary flex-1">
                    Update Subgroup
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* View Members Modal */}
      {showMembersModal && (
        <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in"
             onClick={() => setShowMembersModal(false)}>
          <div className="min-h-full flex items-end sm:items-center justify-center p-0 sm:p-4">
            <div className="modal-content w-full sm:max-w-2xl rounded-t-2xl sm:rounded-2xl animate-modal-enter"
                 onClick={(e) => e.stopPropagation()}>
              <div className="modal-header px-4 sm:px-6 py-4">
                <h2 className="text-lg font-semibold">Members - {viewingSubgroupName}</h2>
              </div>

              <div className="modal-body px-4 sm:px-6 max-h-96 overflow-y-auto">
                {viewingMembers.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No members assigned to this subgroup yet.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {viewingMembers.map((member) => (
                      <div key={member.user_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div>
                          <div className="font-medium text-gray-900">{member.full_name}</div>
                          <div className="text-sm text-gray-600">{member.email}</div>
                          {member.phone_number && (
                            <div className="text-sm text-gray-600">{member.phone_number}</div>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          Joined {new Date(member.joined_at).toLocaleDateString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="modal-footer px-4 sm:px-6 py-4">
                <button
                  onClick={() => setShowMembersModal(false)}
                  className="btn-secondary w-full"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        onClose={() => setDeleteDialog({ isOpen: false, subgroupId: null, subgroupName: '', isLoading: false })}
        onConfirm={handleDeleteSubgroup}
        title="Delete Subgroup"
        message="Are you sure you want to delete this subgroup? All member assignments will be removed."
        itemName={deleteDialog.subgroupName}
        confirmText="Delete Subgroup"
        cancelText="Keep Subgroup"
        variant="danger"
        isLoading={deleteDialog.isLoading}
      />

      {/* Member Assignment Modal */}
      {assignmentSubgroup && (
        <MemberAssignmentModal
          isOpen={showAssignmentModal}
          onClose={() => {
            setShowAssignmentModal(false);
            setAssignmentSubgroup(null);
          }}
          subgroupId={assignmentSubgroup.id}
          subgroupName={assignmentSubgroup.name}
          selectionMode={assignmentSubgroup.selection_mode}
          groupName={group?.name || ''}
          onMemberAssigned={handleMemberAssigned}
        />
      )}
    </div>
  );
}
