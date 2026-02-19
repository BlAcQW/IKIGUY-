/**
 * Main App Component
 * Routing and global providers
 */

import { useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './store/authStore';
import { OrganizationProvider } from './contexts/OrganizationContext';

// Layout
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import RoleProtectedRoute from './components/RoleProtectedRoute';
import OfflineBanner from './components/OfflineBanner';
import PWAInstallPrompt from './components/PWAInstallPrompt';
import { PWAUpdateBanner } from './components/PWAUpdateBanner';

// Core Pages (loaded immediately)
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import AuthCallbackPage from './pages/AuthCallbackPage';
import ProfileCompletionPage from './pages/ProfileCompletionPage';

// Lazy-loaded Pages (loaded on demand)
const BrowsePage = lazy(() => import('./pages/BrowsePage'));
const AllBooksPage = lazy(() => import('./pages/AllBooksPage'));
const LibraryPage = lazy(() => import('./pages/LibraryPage'));
const PlayerPage = lazy(() => import('./pages/PlayerPageRedesign'));
const AudiobookPlayerPage = lazy(() => import('./pages/AudiobookPlayerPage'));
const BookDetailPage = lazy(() => import('./pages/BookDetailPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const WalletPage = lazy(() => import('./pages/WalletPage'));
const VoiceSettingsPage = lazy(() => import('./pages/VoiceSettingsPage'));
const MyBooksPage = lazy(() => import('./pages/MyBooksPage'));
const AuthorUploadPage = lazy(() => import('./pages/AuthorUploadPage'));

// Social Pages (lazy-loaded)
const LeaderboardPage = lazy(() => import('./pages/LeaderboardPage'));
const DiscoverPage = lazy(() => import('./pages/DiscoverPage'));
const ActivityFeedPage = lazy(() => import('./pages/ActivityFeedPage'));
const UserProfilePage = lazy(() => import('./pages/UserProfilePage'));

// Admin Pages (lazy-loaded)
const AdminDashboardPage = lazy(() => import('./pages/AdminDashboardPage'));
const ProviderManagementPage = lazy(() => import('./pages/ProviderManagementPage'));
const AnalyticsDashboardPage = lazy(() => import('./pages/AnalyticsDashboardPage'));
const AdminUserAnalyticsPage = lazy(() => import('./pages/AdminUserAnalyticsPage'));
const OrganizationsPage = lazy(() => import('./pages/admin/OrganizationsPage'));
const AdminSettingsPage = lazy(() => import('./pages/admin/SettingsPage'));
const BillingPage = lazy(() => import('./pages/admin/BillingPage'));
const UsersPage = lazy(() => import('./pages/admin/UsersPage'));
const HiddenBooksPage = lazy(() => import('./pages/admin/HiddenBooksPage'));
const BookModerationPage = lazy(() => import('./pages/admin/BookModerationPage'));

// Loading fallback for lazy-loaded pages
const PageLoader = () => (
	<div className="flex items-center justify-center min-h-screen bg-gray-950">
		<div className="text-center">
			<div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-500 mx-auto mb-3"></div>
			<p className="text-gray-400 text-sm">Loading...</p>
		</div>
	</div>
);

// Create a QueryClient instance
const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			retry: 1,
			refetchOnWindowFocus: false,
			staleTime: 1000 * 60 * 5, // 5 minutes
		},
	},
});

function App() {
	const { initialize, initialized } = useAuthStore();

	useEffect(() => {
		initialize();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []); // Only run once on mount

	if (!initialized) {
		return (
			<div className="flex items-center justify-center min-h-screen bg-gray-900">
				<div className="text-center">
					<div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
					<p className="text-gray-400">Loading...</p>
				</div>
			</div>
		);
	}

	return (
		<QueryClientProvider client={queryClient}>
			<OrganizationProvider>
				<BrowserRouter>
					<Toaster
						position="top-right"
						toastOptions={{
							duration: 3000,
							style: {
								background: '#1f2937',
								color: '#f3f4f6',
								border: '1px solid #374151',
							},
							success: {
								iconTheme: {
									primary: '#10b981',
									secondary: '#f3f4f6',
								},
							},
							error: {
								iconTheme: {
									primary: '#ef4444',
									secondary: '#f3f4f6',
								},
							},
						}}
					/>
					<OfflineBanner />
					<PWAUpdateBanner />
					<PWAInstallPrompt />

					<Suspense fallback={<PageLoader />}>
						<Routes>
							{/* Public routes */}
							<Route path="/login" element={<LoginPage />} />
							<Route path="/signup" element={<SignupPage />} />
							<Route path="/complete-profile" element={<ProfileCompletionPage />} />
							<Route path="/auth/callback" element={<AuthCallbackPage />} />

							{/* Protected routes */}
							<Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
								<Route path="/" element={<HomePage />} />
								<Route path="/browse" element={<BrowsePage />} />
								<Route path="/all-books" element={<AllBooksPage />} />
								<Route path="/library" element={<LibraryPage />} />
								<Route path="/book/:id" element={<BookDetailPage />} />
								<Route path="/player/:bookId" element={<PlayerPage />} />
								<Route path="/audiobook/:bookId" element={<AudiobookPlayerPage />} />
								<Route path="/profile" element={<ProfilePage />} />
								<Route path="/wallet" element={<WalletPage />} />
								<Route path="/voice-settings" element={<VoiceSettingsPage />} />
								<Route path="/my-books" element={
									<RoleProtectedRoute allowedRoles={['author', 'admin', 'superadmin', 'universal_admin']}>
										<MyBooksPage />
									</RoleProtectedRoute>
								} />

								{/* Social Features */}
								<Route path="/leaderboard" element={<LeaderboardPage />} />
								<Route path="/discover" element={<DiscoverPage />} />
								<Route path="/feed" element={<ActivityFeedPage />} />
								<Route path="/user/:userId" element={<UserProfilePage />} />

								<Route path="/author/upload" element={
									<RoleProtectedRoute allowedRoles={['author', 'admin', 'superadmin', 'universal_admin']}>
										<AuthorUploadPage />
									</RoleProtectedRoute>
								} />
							</Route>

							{/* Admin routes (without main layout) */}
							<Route path="/admin" element={<ProtectedRoute><AdminDashboardPage /></ProtectedRoute>} />
							<Route path="/admin/providers" element={<ProtectedRoute><ProviderManagementPage /></ProtectedRoute>} />
							<Route path="/admin/books/upload" element={
								<RoleProtectedRoute allowedRoles={['author', 'admin', 'superadmin', 'universal_admin']}>
									<AuthorUploadPage />
								</RoleProtectedRoute>
							} />
							<Route path="/admin/analytics" element={<ProtectedRoute><AnalyticsDashboardPage /></ProtectedRoute>} />
							<Route path="/admin/analytics/users" element={<ProtectedRoute><AdminUserAnalyticsPage /></ProtectedRoute>} />

							{/* New Organization Admin Routes */}
							<Route path="/admin/organizations" element={<ProtectedRoute><OrganizationsPage /></ProtectedRoute>} />
							<Route path="/admin/settings" element={<ProtectedRoute><AdminSettingsPage /></ProtectedRoute>} />
							<Route path="/admin/billing" element={<ProtectedRoute><BillingPage /></ProtectedRoute>} />
							<Route path="/admin/users" element={<ProtectedRoute><UsersPage /></ProtectedRoute>} />

							{/* Book Moderation Admin Routes */}
							<Route path="/admin/books/moderation" element={
								<RoleProtectedRoute allowedRoles={['admin', 'superadmin', 'universal_admin']}>
									<BookModerationPage />
								</RoleProtectedRoute>
							} />
							<Route path="/admin/books/hidden" element={
								<RoleProtectedRoute allowedRoles={['admin', 'superadmin', 'universal_admin']}>
									<HiddenBooksPage />
								</RoleProtectedRoute>
							} />

							{/* Catch all */}
							<Route path="*" element={<Navigate to="/" replace />} />
						</Routes>
					</Suspense>
				</BrowserRouter>
			</OrganizationProvider>
		</QueryClientProvider>
	);
}

export default App;
