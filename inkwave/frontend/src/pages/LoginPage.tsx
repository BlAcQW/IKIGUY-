/**
 * Login Page
 *
 * Supports book invitation links via ?invite=<token> parameter.
 * When logging in with an invitation, redeems it after successful login.
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { BookOpen, Gift } from 'lucide-react';
import { api } from '../lib/api';
import toast from 'react-hot-toast';

interface InvitationInfo {
  valid: boolean;
  book_title: string;
  book_cover_url?: string;
  book_author?: string;
  welcome_message?: string;
  status: string;
  error_message?: string;
}

export default function LoginPage() {
	useEffect(() => {
		document.title = 'Login - InkWave';
	}, []);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { signIn, loading } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  // Invitation state
  const inviteToken = searchParams.get('invite');
  const [invitationInfo, setInvitationInfo] = useState<InvitationInfo | null>(null);
  const [loadingInvitation, setLoadingInvitation] = useState(false);

  const from = (location.state as any)?.from?.pathname || '/';

  // Fetch invitation info on mount if token present
  useEffect(() => {
    if (inviteToken) {
      fetchInvitationInfo(inviteToken);
    }
  }, [inviteToken]);

  const fetchInvitationInfo = async (token: string) => {
    setLoadingInvitation(true);
    try {
      const response = await api.bookInvitations.getPublicInfo(token);
      setInvitationInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch invitation info:', error);
    } finally {
      setLoadingInvitation(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const { success } = await signIn(email, password);

    if (success) {
      // If we have an invitation token, try to redeem it
      if (inviteToken && invitationInfo?.valid) {
        try {
          const redeemResponse = await api.bookInvitations.redeem(inviteToken);
          if (redeemResponse.data.success) {
            toast.success(`"${redeemResponse.data.book_title}" added to your library!`);
            navigate(`/book/${redeemResponse.data.book_id}`, { replace: true });
            return;
          }
        } catch (error: any) {
          // If already redeemed or other error, just continue
          console.log('Invitation redemption:', error?.response?.data?.detail || 'Already redeemed or error');
        }
      }
      navigate(from, { replace: true });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center space-x-2 text-3xl font-bold">
            <BookOpen className="h-10 w-10 text-purple-400" />
            <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Inkwave
            </span>
          </Link>
          <p className="mt-2 text-gray-400">Welcome back! Sign in to continue your journey.</p>
        </div>

        {/* Invitation Banner (if present) */}
        {invitationInfo?.valid && (
          <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 border border-purple-500/30 rounded-xl p-4 mb-6">
            <div className="flex items-start gap-4">
              {invitationInfo.book_cover_url && (
                <img
                  src={invitationInfo.book_cover_url}
                  alt={invitationInfo.book_title}
                  className="w-16 h-20 object-cover rounded-lg shadow-lg"
                />
              )}
              <div className="flex-1">
                <div className="flex items-center gap-2 text-purple-300 text-sm mb-1">
                  <Gift className="w-4 h-4" />
                  <span>You've been invited!</span>
                </div>
                <h3 className="font-semibold text-white">{invitationInfo.book_title}</h3>
                {invitationInfo.book_author && (
                  <p className="text-gray-400 text-sm">by {invitationInfo.book_author}</p>
                )}
                <p className="text-purple-300 text-xs mt-2">
                  Sign in to add this book to your library
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Login Form */}
        <div className="bg-gray-800 rounded-2xl shadow-2xl p-8">
          <h2 className="text-2xl font-bold text-white mb-6">Sign In</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold py-3 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Sign Up Link */}
          <p className="mt-6 text-center text-gray-400">
            Don't have an account?{' '}
            <Link
              to={inviteToken ? `/signup?invite=${inviteToken}` : '/signup'}
              className="text-purple-400 hover:text-purple-300 font-semibold"
            >
              Sign up for free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
