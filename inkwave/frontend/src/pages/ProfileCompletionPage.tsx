/**
 * Profile Completion Page
 *
 * Shown after signup to collect additional user information.
 * Collects first name, last name, phone number, and date of birth.
 */

import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { BookOpen, User } from 'lucide-react';
import { api } from '../lib/api';
import toast from 'react-hot-toast';

export default function ProfileCompletionPage() {
  useEffect(() => {
    document.title = 'Complete Profile - InkWave';
  }, []);

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('+233');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const bookId = searchParams.get('bookId');
  const fromInvitation = searchParams.get('fromInvitation') === 'true';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Update user profile with additional information
      await api.profile.update({
        first_name: firstName || undefined,
        last_name: lastName || undefined,
        phone_number: phoneNumber && phoneNumber !== '+233' ? phoneNumber : undefined,
        date_of_birth: dateOfBirth || undefined,
      });

      toast.success('Profile completed!');

      // Navigate to the appropriate destination
      if (fromInvitation && bookId) {
        navigate(`/book/${bookId}`, { replace: true });
      } else {
        navigate('/library', { replace: true });
      }
    } catch (error: any) {
      console.error('Profile update error:', error);
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    // Allow user to skip this step
    if (fromInvitation && bookId) {
      navigate(`/book/${bookId}`, { replace: true });
    } else {
      navigate('/library', { replace: true });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center space-x-2 text-3xl font-bold mb-4">
            <BookOpen className="h-10 w-10 text-purple-400" />
            <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Inkwave
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Complete Your Profile</h1>
          <p className="text-gray-400">
            Help us personalize your experience by sharing a bit more about yourself.
          </p>
        </div>

        {/* Profile Form */}
        <div className="bg-gray-800 rounded-2xl shadow-2xl p-8">
          <div className="flex items-center space-x-2 mb-6">
            <User className="h-6 w-6 text-purple-400" />
            <h2 className="text-xl font-bold text-white">Your Information</h2>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* First Name and Last Name */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-gray-300 mb-2">
                  First Name <span className="text-gray-500 text-xs">(optional)</span>
                </label>
                <input
                  id="firstName"
                  type="text"
                  autoComplete="given-name"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="John"
                />
              </div>

              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-gray-300 mb-2">
                  Last Name <span className="text-gray-500 text-xs">(optional)</span>
                </label>
                <input
                  id="lastName"
                  type="text"
                  autoComplete="family-name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Doe"
                />
              </div>
            </div>

            {/* Phone Number */}
            <div>
              <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-300 mb-2">
                Phone Number <span className="text-gray-500 text-xs">(optional)</span>
              </label>
              <input
                id="phoneNumber"
                type="tel"
                autoComplete="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="+233 XX XXX XXXX"
              />
            </div>

            {/* Date of Birth */}
            <div>
              <label htmlFor="dateOfBirth" className="block text-sm font-medium text-gray-300 mb-2">
                Date of Birth <span className="text-gray-500 text-xs">(optional)</span>
              </label>
              <input
                id="dateOfBirth"
                type="date"
                autoComplete="bday"
                value={dateOfBirth}
                onChange={(e) => setDateOfBirth(e.target.value)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {/* Action Buttons */}
            <div className="space-y-3 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold py-3 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Saving...' : 'Complete Profile'}
              </button>

              <button
                type="button"
                onClick={handleSkip}
                className="w-full bg-gray-700 hover:bg-gray-600 text-gray-300 font-medium py-3 px-4 rounded-lg transition"
              >
                Skip for now
              </button>
            </div>
          </form>

          <p className="mt-4 text-center text-sm text-gray-400">
            You can always update this information later in your profile settings.
          </p>
        </div>
      </div>
    </div>
  );
}
