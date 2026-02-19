import React, { useState, useEffect } from 'react';
import { X, UserPlus, Loader2, AlertCircle, Calendar, Heart, Globe } from 'lucide-react';
import { API_ENDPOINTS } from '../../config/api-config';

interface FirstTimerFormData {
  first_name: string;
  last_name: string;
  phone: string;
  email?: string;
  date_of_birth?: string;
  gender?: 'male' | 'female' | 'other';
  address?: string;
  visit_date?: string;
  visit_type: 'first_time' | 'returning';
  service_attended?: string;
  interest_type: 'visitor' | 'new_convert' | 'existing_member' | 'discipleship';
  wants_membership: boolean;
  wants_discipleship: boolean;
  how_heard_about_us?: string;
  invited_by?: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  editingFirstTimer?: any;
}

const FirstTimerFormModal: React.FC<Props> = ({ isOpen, onClose, onSuccess, editingFirstTimer }) => {
  const [formData, setFormData] = useState<FirstTimerFormData>({
    first_name: '',
    last_name: '',
    phone: '',
    visit_type: 'first_time',
    interest_type: 'visitor',
    wants_membership: false,
    wants_discipleship: false,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editingFirstTimer) {
      setFormData({
        first_name: editingFirstTimer.first_name || '',
        last_name: editingFirstTimer.last_name || '',
        phone: editingFirstTimer.phone || '',
        email: editingFirstTimer.email || '',
        date_of_birth: editingFirstTimer.date_of_birth ? new Date(editingFirstTimer.date_of_birth).toISOString().split('T')[0] : '',
        gender: editingFirstTimer.gender || undefined,
        address: editingFirstTimer.address || '',
        visit_date: editingFirstTimer.visit_date ? new Date(editingFirstTimer.visit_date).toISOString().split('T')[0] : '',
        visit_type: editingFirstTimer.visit_type || 'first_time',
        service_attended: editingFirstTimer.service_attended || '',
        interest_type: editingFirstTimer.interest_type || 'visitor',
        wants_membership: editingFirstTimer.wants_membership || false,
        wants_discipleship: editingFirstTimer.wants_discipleship || false,
        how_heard_about_us: editingFirstTimer.how_heard_about_us || '',
        invited_by: editingFirstTimer.invited_by || '',
      });
    } else {
      // Reset form for new entry
      setFormData({
        first_name: '',
        last_name: '',
        phone: '',
        visit_type: 'first_time',
        interest_type: 'visitor',
        wants_membership: false,
        wants_discipleship: false,
      });
    }
    setError(null);
  }, [editingFirstTimer, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');

      // Prepare data - remove empty strings and convert dates
      const dataToSend: any = {
        first_name: formData.first_name,
        last_name: formData.last_name,
        phone: formData.phone,
        visit_type: formData.visit_type,
        interest_type: formData.interest_type,
        wants_membership: formData.wants_membership,
        wants_discipleship: formData.wants_discipleship,
      };

      // Add optional fields if provided
      if (formData.email) dataToSend.email = formData.email;
      if (formData.gender) dataToSend.gender = formData.gender;
      if (formData.address) dataToSend.address = formData.address;
      if (formData.service_attended) dataToSend.service_attended = formData.service_attended;
      if (formData.how_heard_about_us) dataToSend.how_heard_about_us = formData.how_heard_about_us;
      if (formData.invited_by) dataToSend.invited_by = formData.invited_by;

      // Convert dates to ISO format if provided
      if (formData.date_of_birth) {
        dataToSend.date_of_birth = new Date(formData.date_of_birth).toISOString();
      }
      if (formData.visit_date) {
        dataToSend.visit_date = new Date(formData.visit_date).toISOString();
      }

      const url = editingFirstTimer
        ? API_ENDPOINTS.FIRST_TIMERS.BY_ID(editingFirstTimer.id)
        : API_ENDPOINTS.FIRST_TIMERS.BASE;

      const method = editingFirstTimer ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(dataToSend),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to ${editingFirstTimer ? 'update' : 'create'} first timer`);
      }

      onSuccess();
      onClose();
    } catch (err) {
      console.error('Error saving first timer:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full sm:max-w-3xl max-h-[90vh] overflow-hidden transform transition-all duration-200 my-8">
        {/* Header with gradient */}
        <div className={`bg-gradient-to-r ${editingFirstTimer ? 'from-blue-600 via-blue-700 to-indigo-700' : 'from-purple-600 via-purple-700 to-blue-700'} px-6 py-5`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center">
                <UserPlus className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-xl font-bold text-white">
                {editingFirstTimer ? 'Edit First Timer' : 'Add New First Timer'}
              </h2>
            </div>
            <button
              onClick={onClose}
              disabled={loading}
              className="p-2 text-white/80 hover:text-white hover:bg-white/20 rounded-lg transition-all disabled:opacity-50"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="p-6 space-y-6 max-h-[calc(90vh-180px)] overflow-y-auto">
            {error && (
              <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <p className="text-red-800 font-medium">{error}</p>
              </div>
            )}

            {/* Personal Information */}
            <div>
              <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-200">
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <UserPlus className="w-4 h-4 text-purple-600" />
                </div>
                <h3 className="text-lg font-bold text-gray-900">Personal Information</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    First Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    placeholder="John"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Last Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    placeholder="Doe"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    required
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    placeholder="+233244123456"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email || ''}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    placeholder="john.doe@example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    value={formData.date_of_birth || ''}
                    onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Gender
                  </label>
                  <select
                    value={formData.gender || ''}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value as any })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                  >
                    <option value="">Select Gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Address
                  </label>
                  <input
                    type="text"
                    value={formData.address || ''}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    placeholder="Home address"
                  />
                </div>
              </div>
            </div>

            {/* Visit Information */}
            <div>
              <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-200">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Calendar className="w-4 h-4 text-blue-600" />
                </div>
                <h3 className="text-lg font-bold text-gray-900">Visit Information</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Visit Date
                  </label>
                  <input
                    type="date"
                    value={formData.visit_date || ''}
                    onChange={(e) => setFormData({ ...formData, visit_date: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Visit Type
                  </label>
                  <select
                    value={formData.visit_type}
                    onChange={(e) => setFormData({ ...formData, visit_type: e.target.value as any })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                  >
                    <option value="first_time">First Time</option>
                    <option value="returning">Returning</option>
                  </select>
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Service Attended
                  </label>
                  <input
                    type="text"
                    value={formData.service_attended || ''}
                    onChange={(e) => setFormData({ ...formData, service_attended: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    placeholder="Sunday Service, Youth Meeting, etc."
                  />
                </div>
              </div>
            </div>

            {/* Interest & Intent */}
            <div>
              <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-200">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <Heart className="w-4 h-4 text-green-600" />
                </div>
                <h3 className="text-lg font-bold text-gray-900">Interest & Intent</h3>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Interest Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    required
                    value={formData.interest_type}
                    onChange={(e) => setFormData({ ...formData, interest_type: e.target.value as any })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                  >
                    <option value="visitor">Visitor (Just Visiting)</option>
                    <option value="new_convert">New Convert (Wants Membership)</option>
                    <option value="existing_member">Existing Member (Returning)</option>
                    <option value="discipleship">Discipleship (Wants Classes)</option>
                  </select>
                </div>

                <div className="flex items-center gap-6">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.wants_membership}
                      onChange={(e) => setFormData({ ...formData, wants_membership: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Interested in becoming a member</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.wants_discipleship}
                      onChange={(e) => setFormData({ ...formData, wants_discipleship: e.target.checked })}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Interested in discipleship classes</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Discovery */}
            <div>
              <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-200">
                <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                  <Globe className="w-4 h-4 text-amber-600" />
                </div>
                <h3 className="text-lg font-bold text-gray-900">How They Found Us</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    How Heard About Us
                  </label>
                  <input
                    type="text"
                    value={formData.how_heard_about_us || ''}
                    onChange={(e) => setFormData({ ...formData, how_heard_about_us: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    placeholder="Friend, Social Media, etc."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Invited By
                  </label>
                  <input
                    type="text"
                    value={formData.invited_by || ''}
                    onChange={(e) => setFormData({ ...formData, invited_by: e.target.value })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                    placeholder="Name of person who invited them"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2.5 text-gray-700 font-medium border-2 border-gray-300 rounded-lg hover:bg-gray-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`flex-1 px-4 py-2.5 bg-gradient-to-r text-white font-semibold rounded-lg transition-all shadow-lg hover:shadow-xl disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 ${
                editingFirstTimer
                  ? 'from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800'
                  : 'from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800'
              }`}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : editingFirstTimer ? (
                'Update First Timer'
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  Create First Timer
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FirstTimerFormModal;
