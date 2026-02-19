import React, { useState } from 'react';
import { X, UserCheck, AlertCircle, Loader2 } from 'lucide-react';
import { API_ENDPOINTS } from '../../config/api-config';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  firstTimer: {
    id: string;
    full_name: string;
    phone: string;
    email?: string;
    interest_type: string;
    wants_membership: boolean;
    wants_discipleship: boolean;
  } | null;
}

const ConvertToMemberModal: React.FC<Props> = ({ isOpen, onClose, onSuccess, firstTimer }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState('member');

  const handleConvert = async () => {
    if (!firstTimer) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');

      const response = await fetch(API_ENDPOINTS.FIRST_TIMERS.CONVERT_TO_MEMBER(firstTimer.id), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          role,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to convert first timer to member');
      }

      const result = await response.json();

      onSuccess();
      onClose();
    } catch (err) {
      console.error('Error converting first timer:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !firstTimer) return null;

  return (
    <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden transform transition-all duration-200">
        {/* Header with gradient */}
        <div className="bg-gradient-to-r from-green-600 via-green-700 to-emerald-700 px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center">
                <UserCheck className="w-5 h-5 text-white" />
              </div>
              <h2 className="text-xl font-bold text-white">Convert to Member</h2>
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

        {/* Body */}
        <div className="p-6 space-y-5">
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-red-800 font-medium">{error}</p>
            </div>
          )}

          {/* First Timer Information */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-5">
            <h3 className="text-sm font-bold text-blue-900 mb-4 uppercase tracking-wide">First Timer Information</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-blue-200">
                <span className="text-blue-700 font-medium">Name:</span>
                <span className="font-bold text-blue-900">{firstTimer.full_name}</span>
              </div>
              <div className="flex justify-between items-center pb-2 border-b border-blue-200">
                <span className="text-blue-700 font-medium">Phone:</span>
                <span className="font-semibold text-blue-900">{firstTimer.phone}</span>
              </div>
              {firstTimer.email && (
                <div className="flex justify-between items-center pb-2 border-b border-blue-200">
                  <span className="text-blue-700 font-medium">Email:</span>
                  <span className="font-semibold text-blue-900">{firstTimer.email}</span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-blue-700 font-medium">Interest Type:</span>
                <span className="font-semibold text-blue-900 capitalize">{firstTimer.interest_type.replace('_', ' ')}</span>
              </div>
            </div>
          </div>

          {/* Conversion Details */}
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Conversion Details</h3>
              <p className="text-sm text-gray-600 mb-4">
                This will create a member account for <strong>{firstTimer.full_name}</strong>.
                A user profile will be created with the information from this first timer record.
              </p>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Member Role
              </label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all bg-white"
                disabled={loading}
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
              <p className="mt-2 text-xs text-gray-500">
                Select the role for the new member account. This determines their access level in the system.
              </p>
            </div>

            {/* Additional Info */}
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-xl p-5">
              <h4 className="text-sm font-bold text-amber-900 mb-3 flex items-center gap-2">
                <UserCheck className="w-4 h-4" />
                What happens next?
              </h4>
              <ul className="text-sm text-amber-800 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-amber-600 mt-0.5">•</span>
                  <span>A member account will be created with all their information</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-600 mt-0.5">•</span>
                  <span>The first timer record will be marked as "converted"</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-600 mt-0.5">•</span>
                  <span>All information will be transferred to the member profile</span>
                </li>
                {firstTimer.wants_discipleship && (
                  <li className="flex items-start gap-2">
                    <span className="text-amber-600 mt-0.5">•</span>
                    <span>You can enroll them in discipleship classes after conversion</span>
                  </li>
                )}
              </ul>
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
            type="button"
            onClick={handleConvert}
            disabled={loading}
            className="flex-1 px-4 py-2.5 bg-gradient-to-r from-green-600 to-green-700 text-white font-semibold rounded-lg hover:from-green-700 hover:to-green-800 transition-all shadow-lg hover:shadow-xl disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Converting...
              </>
            ) : (
              <>
                <UserCheck className="w-4 h-4" />
                Convert to Member
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConvertToMemberModal;
