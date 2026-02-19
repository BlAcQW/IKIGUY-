import { useState, useEffect } from 'react';
import { Search, X, UserPlus, Trash2, AlertCircle } from 'lucide-react';
import { getApiUrl } from '../../config/api-config';

interface Member {
  id: string;
  full_name: string;
  email: string;
  phone_number?: string;
}

interface AssignedMember extends Member {
  joined_at: string;
}

interface MemberAssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  subgroupId: string;
  subgroupName: string;
  selectionMode: 'single' | 'multi';
  groupName: string;
  onMemberAssigned?: () => void;
}

export default function MemberAssignmentModal({
  isOpen,
  onClose,
  subgroupId,
  subgroupName,
  selectionMode,
  groupName,
  onMemberAssigned
}: MemberAssignmentModalProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Member[]>([]);
  const [assignedMembers, setAssignedMembers] = useState<AssignedMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [assigningMemberId, setAssigningMemberId] = useState<string | null>(null);
  const [removingMemberId, setRemovingMemberId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchAssignedMembers();
    }
  }, [isOpen, subgroupId]);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchQuery.trim().length >= 2) {
        searchMembers();
      } else {
        setSearchResults([]);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  const fetchAssignedMembers = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(getApiUrl(`subgroups/${subgroupId}/members`), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const members = await response.json();
        setAssignedMembers(members.map((m: any) => ({
          id: m.user_id,
          full_name: m.full_name,
          email: m.email,
          phone_number: m.phone_number,
          joined_at: m.joined_at
        })));
      }
    } catch (error) {
      console.error('Error fetching assigned members:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchMembers = async () => {
    setSearching(true);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        getApiUrl(`users?search=${encodeURIComponent(searchQuery)}&limit=20`),
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );

      if (response.ok) {
        const data = await response.json();
        const members = data.users || data;

        // Filter out already assigned members
        const assignedIds = new Set(assignedMembers.map(m => m.id));
        const filteredMembers = members
          .filter((m: any) => !assignedIds.has(m.id || m._id))
          .map((m: any) => ({
            id: m.id || m._id,
            full_name: m.full_name,
            email: m.email,
            phone_number: m.phone_number
          }));

        setSearchResults(filteredMembers);
      }
    } catch (error) {
      console.error('Error searching members:', error);
    } finally {
      setSearching(false);
    }
  };

  const handleAssignMember = async (memberId: string) => {
    setAssigningMemberId(memberId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        getApiUrl(`subgroups/${subgroupId}/assign-member`),
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ user_id: memberId })
        }
      );

      if (response.ok) {
        // Refresh assigned members list
        await fetchAssignedMembers();

        // Clear search
        setSearchQuery('');
        setSearchResults([]);

        // Notify parent component
        if (onMemberAssigned) {
          onMemberAssigned();
        }
      } else {
        const error = await response.json();
        alert(`Failed to assign member: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error assigning member:', error);
      alert('Failed to assign member');
    } finally {
      setAssigningMemberId(null);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!confirm('Are you sure you want to remove this member from the subgroup?')) {
      return;
    }

    setRemovingMemberId(memberId);
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        getApiUrl(`subgroups/${subgroupId}/remove-member`),
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ user_id: memberId })
        }
      );

      if (response.ok) {
        // Refresh assigned members list
        await fetchAssignedMembers();

        // Notify parent component
        if (onMemberAssigned) {
          onMemberAssigned();
        }
      } else {
        const error = await response.json();
        alert(`Failed to remove member: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error removing member:', error);
      alert('Failed to remove member');
    } finally {
      setRemovingMemberId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 overflow-y-auto animate-fade-in"
      onClick={onClose}
    >
      <div className="min-h-full flex items-end sm:items-center justify-center p-0 sm:p-4">
        <div
          className="modal-content w-full sm:max-w-3xl rounded-t-2xl sm:rounded-2xl animate-modal-enter"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="modal-header px-4 sm:px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">Assign Members</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {groupName} &gt; {subgroupName}
                </p>
              </div>
              <button
                onClick={onClose}
                className="btn-icon-sm"
                aria-label="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div className="modal-body px-4 sm:px-6 py-4">
            {/* Warning Banner for Single-Select */}
            {selectionMode === 'single' && (
              <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-blue-900">
                    Single-select subgroup
                  </p>
                  <p className="text-sm text-blue-700 mt-1">
                    Members can only be in ONE subgroup of the "{groupName}" group.
                    Assigning a member here will automatically remove them from other subgroups in this group.
                  </p>
                </div>
              </div>
            )}

            {/* Search Members */}
            <div className="mb-6">
              <label className="label">Search Members to Assign</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="input pl-10"
                  placeholder="Search by name, email, or phone..."
                />
              </div>

              {/* Search Results */}
              {searching && (
                <div className="mt-2 text-sm text-gray-500">Searching...</div>
              )}

              {searchResults.length > 0 && (
                <div className="mt-2 bg-white border border-gray-200 rounded-lg max-h-60 overflow-y-auto">
                  {searchResults.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">
                          {member.full_name}
                        </div>
                        <div className="text-sm text-gray-600 truncate">
                          {member.email}
                        </div>
                        {member.phone_number && (
                          <div className="text-sm text-gray-600">
                            {member.phone_number}
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => handleAssignMember(member.id)}
                        disabled={assigningMemberId === member.id}
                        className="btn-icon-sm text-green-600 hover:bg-green-50 ml-3"
                        title="Assign member"
                      >
                        {assigningMemberId === member.id ? (
                          <span className="text-xs">...</span>
                        ) : (
                          <UserPlus className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {searchQuery.trim().length >= 2 && !searching && searchResults.length === 0 && (
                <div className="mt-2 text-sm text-gray-500">
                  No members found matching "{searchQuery}"
                </div>
              )}
            </div>

            {/* Current Members */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="label mb-0">
                  Current Members ({assignedMembers.length})
                </label>
              </div>

              {loading ? (
                <div className="text-center py-8 text-gray-500">
                  Loading members...
                </div>
              ) : assignedMembers.length === 0 ? (
                <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg">
                  No members assigned yet. Search and assign members above.
                </div>
              ) : (
                <div className="bg-white border border-gray-200 rounded-lg max-h-80 overflow-y-auto">
                  {assignedMembers.map((member) => (
                    <div
                      key={member.id}
                      className="flex items-center justify-between p-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">
                          {member.full_name}
                        </div>
                        <div className="text-sm text-gray-600 truncate">
                          {member.email}
                        </div>
                        {member.phone_number && (
                          <div className="text-sm text-gray-600">
                            {member.phone_number}
                          </div>
                        )}
                        <div className="text-xs text-gray-500 mt-1">
                          Joined {new Date(member.joined_at).toLocaleDateString()}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveMember(member.id)}
                        disabled={removingMemberId === member.id}
                        className="btn-icon-sm text-red-600 hover:bg-red-50 ml-3"
                        title="Remove member"
                      >
                        {removingMemberId === member.id ? (
                          <span className="text-xs">...</span>
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="modal-footer px-4 sm:px-6 py-4 border-t border-gray-200">
            <button onClick={onClose} className="btn-secondary w-full">
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
