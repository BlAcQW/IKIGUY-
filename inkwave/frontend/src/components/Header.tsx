/**
 * Header Component
 *
 * Navigation + Wallet Balance + Profile.
 * Mobile-first responsive design with hamburger menu.
 * Uses centralized navigation config for consistent active state.
 */

import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useWalletStore } from '../store/walletStore';
import { useProfile } from '../hooks/useProfile';
import { useEffect, useState } from 'react';
import { BookOpen, User, Wallet, LogOut, AlertCircle, Building2, ChevronDown, Sparkles, Volume2, Upload, Menu, X, Settings } from 'lucide-react';
import { api } from '../lib/api';
import { MAIN_NAV_ITEMS, ADMIN_NAV_ITEMS, isNavItemActive } from '../config/navigation';

interface UserProfile {
	user_id: string;
	email: string;
	display_name?: string;
	avatar_url?: string;
}

export default function Header() {
	const { user, signOut } = useAuthStore();
	const { balance, isLowBalance, fetchBalance } = useWalletStore();
	const { data: profileData } = useProfile();
	const navigate = useNavigate();
	const location = useLocation();
	const [profile, setProfile] = useState<UserProfile | null>(null);
	const [loadingProfile, setLoadingProfile] = useState(false);
	const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
	const [profileMenuOpen, setProfileMenuOpen] = useState(false);

	// Check if user has access to admin, voice settings, or wallet
	// Default to false if profileData is not loaded yet
	const canAccessAdmin = profileData ? (profileData.is_admin || profileData.role === 'admin' || profileData.role === 'superadmin') : false;
	const canAccessVoiceSettings = profileData ? (canAccessAdmin || profileData.role === 'author') : false;
	const canAccessWallet = profileData ? (canAccessAdmin || profileData.role === 'author') : false;

	// Load profile data with avatar
	useEffect(() => {
		const loadProfile = async () => {
			if (user) {
				try {
					setLoadingProfile(true);
					const response = await api.profile.get();
					setProfile(response.data);
				} catch (error) {
					console.error('Failed to load profile:', error);
				} finally {
					setLoadingProfile(false);
				}
			}
		};

		loadProfile();
	}, [user]);

	useEffect(() => {
		if (user) {
			fetchBalance();
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [user]); // Only re-fetch when user changes, not when fetchBalance reference changes

	const handleSignOut = async () => {
		await signOut();
		navigate('/login');
	};

	const balanceInDollars = (balance / 100).toFixed(2);

	// Display name or email
	const displayName = profile?.display_name || user?.email?.split('@')[0] || 'Guest User';

	// Navigation links from centralized config
	// Admins see extended navigation, regular users see main nav items
	const navLinks = canAccessAdmin ? ADMIN_NAV_ITEMS : MAIN_NAV_ITEMS;

	// Close mobile menu when route changes
	useEffect(() => {
		setMobileMenuOpen(false);
		setProfileMenuOpen(false);
	}, [location.pathname]);

	return (
		<>
			<header className="sticky top-0 z-50 bg-gray-900/95 backdrop-blur-md border-b border-gray-800">
				<div className="container mx-auto px-3 sm:px-4">
					<div className="flex items-center justify-between h-14 sm:h-16">
						{/* Mobile Menu Button */}
						<button
							onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
							className="md:hidden p-2 -ml-2 hover:bg-gray-800 active:bg-gray-700 rounded-lg transition touch-feedback no-zoom"
							aria-label="Toggle menu"
						>
							{mobileMenuOpen ? (
								<X className="h-6 w-6 text-gray-300" />
							) : (
								<Menu className="h-6 w-6 text-gray-300" />
							)}
						</button>

						{/* Logo */}
						<Link to="/" className="flex items-center space-x-2 text-xl sm:text-2xl font-bold">
							<BookOpen className="h-6 w-6 sm:h-8 sm:w-8 text-purple-500" />
							<span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
								Inkwave
							</span>
						</Link>

						{/* Desktop Navigation Links */}
						<nav className="hidden md:flex items-center space-x-1">
							{navLinks.map((link) => {
								const Icon = link.icon;
								const isActive = isNavItemActive(link, location.pathname);
								return (
									<Link
										key={link.path}
										to={link.path}
										className={`flex items-center space-x-2 px-3 lg:px-4 py-2 rounded-lg transition ${isActive
											? 'bg-purple-500/20 text-purple-300'
											: 'text-gray-300 hover:bg-gray-800 hover:text-white'
											}`}
									>
										<Icon className="h-4 w-4" />
										<span className="hidden lg:inline">{link.label}</span>
									</Link>
								);
							})}
						</nav>

						{/* Right side */}
						<div className="flex items-center space-x-2 sm:space-x-4">
							{/* Wallet Balance - Compact on mobile - Only show if user has access */}
							{canAccessWallet && (
								<Link
									to="/wallet"
									className={`flex items-center space-x-1 sm:space-x-2 px-2 sm:px-4 py-1.5 sm:py-2 rounded-lg transition text-sm sm:text-base touch-feedback no-zoom ${isLowBalance
										? 'bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 active:bg-red-500/30'
										: 'bg-purple-500/10 border border-purple-500/30 text-purple-300 hover:bg-purple-500/20 active:bg-purple-500/30'
										}`}
								>
									{isLowBalance && <AlertCircle className="h-3 w-3 sm:h-4 sm:w-4" />}
									<Wallet className="h-4 w-4 sm:h-5 sm:w-5" />
									<span className="font-semibold">${balanceInDollars}</span>
								</Link>
							)}

							{/* Profile Button - Click to toggle on mobile */}
							<div className="relative">
								<button
									onClick={() => setProfileMenuOpen(!profileMenuOpen)}
									className="flex items-center space-x-2 sm:space-x-3 px-2 sm:px-3 py-1.5 sm:py-2 rounded-xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/30 hover:border-purple-500/50 active:border-purple-500/70 active:from-purple-500/20 active:to-pink-500/20 transition-all hover:shadow-lg hover:shadow-purple-500/20 touch-feedback no-zoom"
								>
									{/* Avatar */}
									<div className="relative">
										{profile?.avatar_url ? (
											<img
												src={profile.avatar_url}
												alt="Profile"
												className="h-7 w-7 sm:h-8 sm:w-8 rounded-full object-cover ring-2 ring-purple-500/50"
											/>
										) : (
											<div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
												<User className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-white" />
											</div>
										)}
										{/* Personalization indicator dot */}
										<div className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 sm:h-3 sm:w-3 bg-green-400 rounded-full border-2 border-gray-900 animate-pulse"></div>
									</div>

									{/* Name and dropdown indicator - Desktop only */}
									<div className="hidden md:flex items-center space-x-2">
										<span className="font-medium text-white text-sm">{displayName}</span>
										<ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${profileMenuOpen ? 'rotate-180' : ''}`} />
									</div>
								</button>

								{/* Dropdown Menu - Click controlled */}
								{profileMenuOpen && (
									<>
										{/* Backdrop to close menu */}
										<div
											className="fixed inset-0 z-40"
											onClick={() => setProfileMenuOpen(false)}
										/>
										<div className="absolute right-0 mt-2 w-56 sm:w-64 bg-gray-800 rounded-xl shadow-2xl border border-purple-500/30 z-50">
											{/* User Info Header */}
											<div className="px-4 py-3 border-b border-gray-700 bg-gradient-to-r from-purple-500/5 to-pink-500/5 rounded-t-xl">
												<p className="text-sm font-semibold text-white truncate">{displayName}</p>
												<p className="text-xs text-gray-400 truncate">{user?.email || 'guest@inkwave.com'}</p>
											</div>

											{/* Profile Link - Highlighted */}
											<Link
												to="/profile"
												onClick={() => setProfileMenuOpen(false)}
												className="block px-4 py-3 hover:bg-purple-500/10 transition"
											>
												<div className="flex items-center space-x-3">
													<div className="h-8 w-8 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center">
														<Sparkles className="h-4 w-4 text-purple-400" />
													</div>
													<div className="flex-1">
														<p className="text-sm font-medium text-white">My Profile</p>
														<p className="text-xs text-gray-400">Personalized for you</p>
													</div>
												</div>
											</Link>

											{canAccessWallet && (
												<Link
													to="/wallet"
													onClick={() => setProfileMenuOpen(false)}
													className="block px-4 py-3 hover:bg-gray-700 transition flex items-center space-x-3"
												>
													<Wallet className="h-4 w-4 text-gray-400" />
													<span className="text-sm text-gray-300">Wallet</span>
												</Link>
											)}

											{canAccessVoiceSettings && (
												<Link
													to="/voice-settings"
													onClick={() => setProfileMenuOpen(false)}
													className="block px-4 py-3 hover:bg-gray-700 transition flex items-center space-x-3"
												>
													<Volume2 className="h-4 w-4 text-gray-400" />
													<span className="text-sm text-gray-300">Voice Settings</span>
												</Link>
											)}

											<Link
												to="/my-books"
												onClick={() => setProfileMenuOpen(false)}
												className="block px-4 py-3 hover:bg-gray-700 transition flex items-center space-x-3"
											>
												<Upload className="h-4 w-4 text-gray-400" />
												<span className="text-sm text-gray-300">My Books</span>
											</Link>

											{/* Admin Links - Only show if user has admin access */}
											{canAccessAdmin && (
												<>
													<div className="border-t border-gray-700 my-1"></div>
													<Link
														to="/admin"
														onClick={() => setProfileMenuOpen(false)}
														className="block px-4 py-3 hover:bg-gray-700 transition flex items-center space-x-3"
													>
														<Settings className="h-4 w-4 text-gray-400" />
														<span className="text-sm text-gray-300">Admin</span>
													</Link>
													<Link
														to="/admin/organizations"
														onClick={() => setProfileMenuOpen(false)}
														className="block px-4 py-3 hover:bg-gray-700 transition flex items-center space-x-3"
													>
														<Building2 className="h-4 w-4 text-gray-400" />
														<span className="text-sm text-gray-300">Organizations</span>
													</Link>
												</>
											)}

											<div className="border-t border-gray-700 my-1"></div>
											<button
												onClick={() => {
													setProfileMenuOpen(false);
													handleSignOut();
												}}
												className="w-full text-left px-4 py-3 hover:bg-red-500/10 transition flex items-center space-x-3 text-red-400 rounded-b-xl"
											>
												<LogOut className="h-4 w-4" />
												<span className="text-sm">Sign Out</span>
											</button>
										</div>
									</>
								)}
							</div>
						</div>
					</div>
				</div>

				{/* Low Balance Banner - Only show if user has wallet access */}
				{isLowBalance && canAccessWallet && (
					<div className="bg-red-500/10 border-t border-red-500/30 py-2 px-4">
						<p className="text-center text-xs sm:text-sm text-red-400">
							Low balance! <Link to="/wallet" className="underline font-semibold">Top up now</Link> to continue reading.
						</p>
					</div>
				)}
			</header>

			{/* Mobile Navigation Drawer */}
			{mobileMenuOpen && (
				<>
					{/* Backdrop */}
					<div
						className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
						onClick={() => setMobileMenuOpen(false)}
					/>

					{/* Drawer */}
					<nav className="fixed top-14 left-0 right-0 bg-gray-900 border-b border-gray-800 z-40 md:hidden shadow-xl">
						<div className="px-4 py-4 space-y-1">
							{navLinks.map((link) => {
								const Icon = link.icon;
								const isActive = isNavItemActive(link, location.pathname);
								return (
									<Link
										key={link.path}
										to={link.path}
										onClick={() => setMobileMenuOpen(false)}
										className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition touch-feedback no-zoom ${isActive
											? 'bg-purple-500/20 text-purple-300 active:bg-purple-500/30'
											: 'text-gray-300 hover:bg-gray-800 hover:text-white active:bg-gray-700'
											}`}
									>
										<Icon className="h-5 w-5" />
										<span className="font-medium">{link.label}</span>
									</Link>
								);
							})}
						</div>
					</nav>
				</>
			)}
		</>
	);
}
