/**
 * Signup Page
 *
 * Supports book invitation links via ?invite=<token> parameter.
 * When a valid invitation is present, displays book info and grants access on signup.
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { BookOpen, Sparkles, Gift, AlertCircle } from 'lucide-react';
import { FREE_TRIAL_CREDITS } from '../config/constants';
import { api } from '../lib/api';

interface InvitationInfo {
  valid: boolean;
  book_title: string;
  book_cover_url?: string;
  book_author?: string;
  welcome_message?: string;
  status: string;
  error_message?: string;
}

export default function SignupPage() {
	useEffect(() => {
		document.title = 'Sign Up - InkWave';
	}, []);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const { signUp, loading, user, session } = useAuthStore();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Invitation state
  const inviteToken = searchParams.get('invite');
  const [invitationInfo, setInvitationInfo] = useState<InvitationInfo | null>(null);
  const [loadingInvitation, setLoadingInvitation] = useState(false);
  const [redeeming, setRedeeming] = useState(false);

  // Check if user is already logged in and handle invitation automatically
  useEffect(() => {
    const handleLoggedInUserInvitation = async () => {
      if (user && session && inviteToken) {
        // User is already logged in with an invitation link
        setRedeeming(true);
        try {
          // Redeem the invitation
          const response = await api.bookInvitations.redeem(inviteToken);
          const bookId = response.data.book_id;

          // Redirect to book detail page
          navigate(`/book/${bookId}`, { replace: true });
        } catch (error: any) {
          console.error('Failed to redeem invitation:', error);
          // If already redeemed or book already in library, still navigate to home
          if (error.response?.status === 400) {
            // Try to extract book_id from invitation info
            const inviteResponse = await api.bookInvitations.getPublicInfo(inviteToken);
            const bookId = inviteResponse.data.book_id;
            if (bookId) {
              navigate(`/book/${bookId}`, { replace: true });
            } else {
              navigate('/', { replace: true });
            }
          } else {
            navigate('/', { replace: true });
          }
        } finally {
          setRedeeming(false);
        }
      }
    };

    handleLoggedInUserInvitation();
  }, [user, session, inviteToken, navigate]);

  // Fetch invitation info on mount if token present
  useEffect(() => {
    if (inviteToken && !user) {
      fetchInvitationInfo(inviteToken);
    }
  }, [inviteToken, user]);

  const fetchInvitationInfo = async (token: string) => {
    setLoadingInvitation(true);
    try {
      const response = await api.bookInvitations.getPublicInfo(token);
      setInvitationInfo(response.data);
    } catch (error) {
      console.error('Failed to fetch invitation info:', error);
      setInvitationInfo({
        valid: false,
        book_title: '',
        status: 'error',
        error_message: 'Failed to load invitation details',
      });
    } finally {
      setLoadingInvitation(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }

    // Pass invitation token if present and valid
    const token = invitationInfo?.valid ? inviteToken || undefined : undefined;
    const result = await signUp(email, password, token);

    if (result.success) {
      // Redirect to profile completion page with invitation context
      const params = new URLSearchParams();
      if (result.invitationRedeemed && result.libraryBook) {
        params.set('bookId', result.libraryBook.book_id);
        params.set('fromInvitation', 'true');
      }
      navigate(`/complete-profile?${params.toString()}`, { replace: true });
    }
  };

  // Show loading screen while redeeming invitation for logged-in users
  if (redeeming) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-purple-500/20 rounded-full mb-6">
            <Gift className="w-10 h-10 text-purple-400 animate-bounce" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Adding book to your library...</h2>
          <p className="text-gray-400">Please wait while we set up your access</p>
          <div className="mt-6 flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          </div>
        </div>
      </div>
    );
  }

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
          <p className="mt-2 text-gray-400">Start your interactive reading journey today.</p>
        </div>

        {/* Invitation Banner (if present) */}
        {loadingInvitation && (
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 mb-6 animate-pulse">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-16 bg-gray-700 rounded"></div>
              <div className="flex-1">
                <div className="h-4 bg-gray-700 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-700 rounded w-1/2"></div>
              </div>
            </div>
          </div>
        )}

        {invitationInfo && !loadingInvitation && (
          invitationInfo.valid ? (
            <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-xl p-4 mb-6">
              <div className="flex items-start space-x-3">
                {invitationInfo.book_cover_url ? (
                  <img
                    src={invitationInfo.book_cover_url}
                    alt={invitationInfo.book_title}
                    className="w-12 h-16 object-cover rounded shadow-lg"
                  />
                ) : (
                  <div className="w-12 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded flex items-center justify-center">
                    <BookOpen className="h-6 w-6 text-white" />
                  </div>
                )}
                <div className="flex-1">
                  <div className="flex items-center space-x-2 text-green-300 mb-1">
                    <Gift className="h-4 w-4" />
                    <span className="text-sm font-semibold">You've been invited!</span>
                  </div>
                  <p className="text-white font-medium">{invitationInfo.book_title}</p>
                  {invitationInfo.book_author && (
                    <p className="text-gray-400 text-sm">by {invitationInfo.book_author}</p>
                  )}
                  {invitationInfo.welcome_message && (
                    <p className="text-gray-300 text-sm mt-2 italic">"{invitationInfo.welcome_message}"</p>
                  )}
                </div>
              </div>
              <p className="text-green-400/80 text-sm mt-3">
                Sign up to get instant access to this audiobook!
              </p>
            </div>
          ) : (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
              <div className="flex items-center space-x-2 text-red-300">
                <AlertCircle className="h-5 w-5" />
                <span className="font-semibold">Invalid Invitation</span>
              </div>
              <p className="text-gray-400 text-sm mt-1">
                {invitationInfo.error_message || 'This invitation link is no longer valid.'}
              </p>
              <p className="text-gray-500 text-sm mt-2">
                You can still sign up for a regular account below.
              </p>
            </div>
          )
        )}

        {/* Free Trial Banner (only show if no valid invitation) */}
        {(!invitationInfo || !invitationInfo.valid) && !loadingInvitation && (
          <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-xl p-4 mb-6">
            <div className="flex items-center space-x-2 text-purple-300">
              <Sparkles className="h-5 w-5" />
              <span className="font-semibold">Get {FREE_TRIAL_CREDITS} credits free ($2 value)</span>
            </div>
            <p className="text-sm text-gray-400 mt-1">No credit card required • Start listening immediately</p>
          </div>
        )}

        {/* Signup Form */}
        <div className="bg-gray-800 rounded-2xl shadow-2xl p-8">
          <h2 className="text-2xl font-bold text-white mb-6">Create Account</h2>

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
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="••••••••"
                minLength={6}
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-300 mb-2">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                required
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="••••••••"
                minLength={6}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold py-3 px-4 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          {/* Login Link */}
          <p className="mt-6 text-center text-gray-400">
            Already have an account?{' '}
            <Link
              to={inviteToken ? `/login?invite=${inviteToken}` : '/login'}
              className="text-purple-400 hover:text-purple-300 font-semibold"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
