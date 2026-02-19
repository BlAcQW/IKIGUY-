/**
 * ProfilePageEnhanced
 * User profile and settings with backend integration
 */

import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useAuthStore } from '../store/authStore';
import { useWalletStore } from '../store/walletStore';
import { api } from '../lib/api';
import {
	User,
	Mail,
	LogOut,
	Bell,
	Volume2,
	Languages,
	Moon,
	Shield,
	CreditCard,
	BookOpen,
	Mic,
	Save,
	Loader,
	Check,
	Upload,
	Link as LinkIcon,
	Camera,
	BarChart3,
	Clock,
	MessageCircle,
	Calendar,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { PWACacheSettings } from '../components/PWACacheSettings';

// Profile types
interface UserProfile {
	user_id: string;
	email: string;
	display_name?: string;
	avatar_url?: string;
	profile: {
		preferred_voice: string;
		playback_speed: number;
		reading_level: string;
		voice_preferences: {
			provider_id: string;
			voice_id: string;
			speed: number;
			language: string;
			voice_clone_reference?: string;
		};
		interaction_preferences: {
			explanation_depth: string;
			discussion_topics: string[];
		};
	};
	wallet_id?: string;
	credits: number;
	is_admin: boolean;
	created_at: string;
	last_active: string;
}

export default function ProfilePageEnhanced() {
	useEffect(() => {
		document.title = 'Profile - InkWave';
	}, []);

	const { user, signOut } = useAuthStore();
	const { balance } = useWalletStore();

	// Profile state
	const [profile, setProfile] = useState<UserProfile | null>(null);
	const [loading, setLoading] = useState(true);
	const [saving, setSaving] = useState(false);

	// Form state
	const [displayName, setDisplayName] = useState('');
	const [readingLevel, setReadingLevel] = useState('intermediate');
	const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
	const [voiceProvider, setVoiceProvider] = useState('coqui_xtts');
	const [voiceId, setVoiceId] = useState('nova');
	const [language, setLanguage] = useState('en');
	const [explanationDepth, setExplanationDepth] = useState('detailed');
	const [discussionTopics, setDiscussionTopics] = useState<string[]>([
		'themes',
		'characters',
		'context',
	]);

	// Avatar state
	const [avatarUrl, setAvatarUrl] = useState('');
	const [showAvatarModal, setShowAvatarModal] = useState(false);
	const [avatarUrlInput, setAvatarUrlInput] = useState('');
	const [uploadingAvatar, setUploadingAvatar] = useState(false);
	const fileInputRef = useRef<HTMLInputElement>(null);

	// Stats state
	const [stats, setStats] = useState<{ books_started: number; questions_asked: number; listening_time_minutes: number } | null>(null);

	// Consumption stats state (from unified tracking)
	const [consumptionStats, setConsumptionStats] = useState<{
		total_books_opened: number;
		total_books_completed: number;
		total_books_in_progress: number;
		total_listening_time_seconds: number;
		total_ai_narration_time_seconds: number;
		total_reading_time_seconds: number;
		average_session_minutes: number;
	} | null>(null);

	// Listening history state
	const [listeningHistory, setListeningHistory] = useState<{
		total_listening_hours: number;
		total_books: number;
		books: Array<{
			book_id: string;
			book_title: string;
			listening_hours: number;
			listening_minutes: number;
			session_count: number;
			last_listened: string | null;
		}>;
	} | null>(null);
	const [loadingHistory, setLoadingHistory] = useState(false);
	const [showAllBooks, setShowAllBooks] = useState(false);

	// Local UI settings (not saved to backend)
	const [notifications, setNotifications] = useState(true);
	const [autoPlay, setAutoPlay] = useState(true);

	// Load profile from backend
	useEffect(() => {
		loadProfile();
		loadStats();
		loadListeningHistory();
		loadConsumptionStats();

		// Refresh stats every 15 seconds to show updated listening time
		const statsInterval = setInterval(() => {
			console.log('[Profile] Auto-refreshing stats...');
			loadStats();
			loadConsumptionStats();
		}, 15000); // 15 seconds (faster refresh)

		return () => clearInterval(statsInterval);
	}, []);

	const loadProfile = async () => {
		try {
			setLoading(true);
			const response = await api.profile.get();
			const profileData = response.data;

			setProfile(profileData);

			// Populate form with profile data
			setDisplayName(profileData.display_name || '');
			setAvatarUrl(profileData.avatar_url || '');
			setReadingLevel(profileData.profile.reading_level);
			setPlaybackSpeed(profileData.profile.playback_speed);
			setVoiceProvider(profileData.profile.voice_preferences.provider_id);
			setVoiceId(profileData.profile.voice_preferences.voice_id);
			setLanguage(profileData.profile.voice_preferences.language);
			setExplanationDepth(profileData.profile.interaction_preferences.explanation_depth);
			setDiscussionTopics(profileData.profile.interaction_preferences.discussion_topics);
		} catch (error: any) {
			console.error('Failed to load profile:', error);
			toast.error('Failed to load profile');
		} finally {
			setLoading(false);
		}
	};

	const loadListeningHistory = async () => {
		try {
			setLoadingHistory(true);
			const response = await api.leaderboard.getMyHistory();
			setListeningHistory(response.data);
		} catch (error: any) {
			console.error('Failed to load listening history:', error);
		} finally {
			setLoadingHistory(false);
		}
	};

	const loadStats = async () => {
		try {
			console.log('[Profile] Fetching stats...');
			const response = await api.profile.getStats();
			console.log('[Profile] Stats response:', response.data);
			const newStats = response.data;

			// Force update even if values appear the same
			setStats(prev => {
				console.log('[Profile] Previous stats:', prev);
				console.log('[Profile] New stats:', newStats);
				console.log('[Profile] Listening time changed:', prev?.listening_time_minutes !== newStats.listening_time_minutes);
				return newStats;
			});
		} catch (error: any) {
			console.error('[Profile] Failed to load stats:', error);
			// Don't show error toast for stats, it's not critical
		}
	};

	const loadConsumptionStats = async () => {
		try {
			const response = await api.consumption.getMyStats(30); // Last 30 days
			if (response.data) {
				setConsumptionStats(response.data);
			}
		} catch (error: any) {
			console.error('[Profile] Failed to load consumption stats:', error);
			// Don't show error toast, consumption tracking may not have data yet
		}
	};

	const handleSaveProfile = async () => {
		try {
			setSaving(true);

			// Update profile
			await api.profile.update({
				display_name: displayName,
				reading_level: readingLevel,
				playback_speed: playbackSpeed,
				voice_preferences: {
					provider_id: voiceProvider,
					voice_id: voiceId,
					speed: playbackSpeed,
					language: language,
				},
				interaction_preferences: {
					explanation_depth: explanationDepth,
					discussion_topics: discussionTopics,
				},
			});

			toast.success('Profile updated successfully!');

			// Reload profile to get updated data
			await loadProfile();
		} catch (error: any) {
			console.error('Failed to save profile:', error);
			toast.error(error.response?.data?.detail || 'Failed to save profile');
		} finally {
			setSaving(false);
		}
	};

	const handleSignOut = async () => {
		if (window.confirm('Are you sure you want to sign out?')) {
			await signOut();
			toast.success('Signed out successfully');
		}
	};

	const handleNotificationToggle = () => {
		setNotifications(!notifications);
		toast.success(
			notifications ? 'Notifications disabled' : 'Notifications enabled'
		);
	};

	const handleAutoPlayToggle = () => {
		setAutoPlay(!autoPlay);
		toast.success(autoPlay ? 'Auto-play disabled' : 'Auto-play enabled');
	};

	const handleTopicToggle = (topic: string) => {
		if (discussionTopics.includes(topic)) {
			setDiscussionTopics(discussionTopics.filter((t) => t !== topic));
		} else {
			setDiscussionTopics([...discussionTopics, topic]);
		}
	};

	const handleAvatarFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
		const file = event.target.files?.[0];
		if (!file) return;

		try {
			setUploadingAvatar(true);
			const response = await api.profile.uploadAvatar(file);
			setAvatarUrl(response.data.avatar_url);
			setProfile(prev => prev ? { ...prev, avatar_url: response.data.avatar_url } : prev);
			toast.success('Avatar uploaded successfully!');
			setShowAvatarModal(false);
		} catch (error: any) {
			console.error('Failed to upload avatar:', error);
			toast.error(error.response?.data?.detail || 'Failed to upload avatar');
		} finally {
			setUploadingAvatar(false);
		}
	};

	const handleAvatarUrlSubmit = async () => {
		if (!avatarUrlInput.trim()) {
			toast.error('Please enter a valid URL');
			return;
		}

		try {
			setUploadingAvatar(true);
			const response = await api.profile.updateAvatarUrl(avatarUrlInput);
			setAvatarUrl(response.data.avatar_url);
			setProfile(prev => prev ? { ...prev, avatar_url: response.data.avatar_url } : prev);
			toast.success('Avatar updated successfully!');
			setShowAvatarModal(false);
			setAvatarUrlInput('');
		} catch (error: any) {
			console.error('Failed to update avatar URL:', error);
			toast.error(error.response?.data?.detail || 'Failed to update avatar URL');
		} finally {
			setUploadingAvatar(false);
		}
	};

	const createdDate = profile?.created_at
		? new Date(profile.created_at).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
		})
		: 'Unknown';

	if (loading) {
		return (
			<div className="min-h-screen bg-gray-950 flex items-center justify-center">
				<Loader className="h-12 w-12 text-purple-400 animate-spin" />
			</div>
		);
	}

	return (
		<motion.div
			initial={{ opacity: 0 }}
			animate={{ opacity: 1 }}
			transition={{ duration: 0.5 }}
			className="min-h-screen bg-gray-950 py-12 px-4"
		>
			<div className="max-w-4xl mx-auto space-y-8">
				{/* Header */}
				<div className="flex justify-between items-center">
					<div>
						<h1 className="text-4xl font-bold text-white mb-2">Profile & Settings</h1>
						<p className="text-gray-400">Personalize your reading experience</p>
					</div>
					<button
						onClick={handleSaveProfile}
						disabled={saving}
						className="flex items-center space-x-2 px-6 py-3 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-600 text-white rounded-lg transition"
					>
						{saving ? (
							<>
								<Loader className="h-5 w-5 animate-spin" />
								<span>Saving...</span>
							</>
						) : (
							<>
								<Save className="h-5 w-5" />
								<span>Save Changes</span>
							</>
						)}
					</button>
				</div>

				{/* Profile Card */}
				<motion.div
					initial={{ opacity: 0, y: 20 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ delay: 0.1 }}
					className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/30 rounded-2xl p-8"
				>
					<div className="flex flex-col sm:flex-row items-center sm:items-start space-y-4 sm:space-y-0 sm:space-x-6">
						{/* Avatar */}
						<div className="relative group">
							{avatarUrl ? (
								<img
									src={avatarUrl}
									alt="Avatar"
									className="h-24 w-24 rounded-2xl object-cover"
								/>
							) : (
								<div className="p-6 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-2xl">
									<User className="h-12 w-12 text-purple-400" />
								</div>
							)}
							<button
								onClick={() => setShowAvatarModal(true)}
								className="absolute inset-0 bg-black/50 rounded-2xl opacity-0 group-hover:opacity-100 transition flex items-center justify-center"
							>
								<Camera className="h-6 w-6 text-white" />
							</button>
						</div>

						<div className="flex-1 text-center sm:text-left space-y-4">
							<div>
								<label className="text-sm text-gray-400 block mb-1">Display Name</label>
								<input
									type="text"
									value={displayName}
									onChange={(e) => setDisplayName(e.target.value)}
									placeholder="Enter your name"
									className="w-full bg-gray-800 text-white px-4 py-2 rounded-lg border border-gray-700 focus:border-purple-500 focus:outline-none"
								/>
							</div>
							<div className="flex items-center justify-center sm:justify-start space-x-2 text-gray-400">
								<Mail className="h-4 w-4" />
								<span>{profile?.email}</span>
							</div>
							<div className="flex flex-wrap gap-4 justify-center sm:justify-start">
								<div className="bg-gray-800/50 rounded-lg px-4 py-2">
									<p className="text-xs text-gray-400">Member Since</p>
									<p className="text-sm font-semibold text-white">{createdDate}</p>
								</div>
								<div className="bg-gray-800/50 rounded-lg px-4 py-2">
									<p className="text-xs text-gray-400">Balance</p>
									<p className="text-sm font-semibold text-white">
										${(balance / 100).toFixed(2)}
									</p>
								</div>
								<div className="bg-gray-800/50 rounded-lg px-4 py-2">
									<p className="text-xs text-gray-400">Credits</p>
									<p className="text-sm font-semibold text-white">{profile?.credits || 0}</p>
								</div>
							</div>
						</div>
					</div>
				</motion.div>

				{/* Stats Card */}
				{stats && (
					<motion.div
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ delay: 0.15 }}
						className="bg-gray-800 rounded-xl p-6"
					>
						<div className="flex items-center justify-between mb-4">
							<h3 className="text-xl font-semibold text-white flex items-center space-x-2">
								<BarChart3 className="h-5 w-5 text-purple-400" />
								<span>Reading Statistics</span>
							</h3>
							<button
								onClick={() => loadStats()}
								className="text-sm text-gray-400 hover:text-white transition-colors"
								title="Refresh stats"
							>
								Refresh
							</button>
						</div>
						<div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
							<div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-lg p-4">
								<div className="flex items-center space-x-3">
									<BookOpen className="h-8 w-8 text-purple-400" />
									<div>
										<p className="text-2xl font-bold text-white">{stats.books_started}</p>
										<p className="text-sm text-gray-400">Books Started</p>
									</div>
								</div>
							</div>
							<div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-lg p-4">
								<div className="flex items-center space-x-3">
									<MessageCircle className="h-8 w-8 text-blue-400" />
									<div>
										<p className="text-2xl font-bold text-white">{stats.questions_asked}</p>
										<p className="text-sm text-gray-400">Questions Asked</p>
									</div>
								</div>
							</div>
							<div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-lg p-4">
								<div className="flex items-center space-x-3">
									<Clock className="h-8 w-8 text-green-400" />
									<div>
										<p className="text-2xl font-bold text-white" key={`stats-${stats.listening_time_minutes || 0}`}>
											{Math.floor((stats.listening_time_minutes || 0) / 60)}h {(stats.listening_time_minutes || 0) % 60}m
										</p>
										<p className="text-sm text-gray-400">Listening Time</p>
										<p className="text-xs text-gray-500 mt-1">
											{stats.listening_time_minutes || 0} total minutes
										</p>
									</div>
								</div>
							</div>
						</div>
					</motion.div>
				)}

				{/* Consumption Activity Card (from unified tracking) */}
				{consumptionStats && (
					<motion.div
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ delay: 0.17 }}
						className="bg-gray-800 rounded-xl p-6"
					>
						<div className="flex items-center justify-between mb-4">
							<h3 className="text-xl font-semibold text-white flex items-center space-x-2">
								<Mic className="h-5 w-5 text-cyan-400" />
								<span>Consumption Activity (30 Days)</span>
							</h3>
							<button
								onClick={() => loadConsumptionStats()}
								className="text-sm text-gray-400 hover:text-white transition-colors"
								title="Refresh consumption stats"
							>
								Refresh
							</button>
						</div>
						<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
							<div className="bg-gradient-to-br from-cyan-500/10 to-blue-500/10 rounded-lg p-4">
								<div className="flex items-center space-x-3">
									<BookOpen className="h-8 w-8 text-cyan-400" />
									<div>
										<p className="text-2xl font-bold text-white">{consumptionStats.total_books_completed}</p>
										<p className="text-sm text-gray-400">Books Completed</p>
										<p className="text-xs text-gray-500 mt-1">
											{consumptionStats.total_books_in_progress} in progress
										</p>
									</div>
								</div>
							</div>
							<div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-lg p-4">
								<div className="flex items-center space-x-3">
									<Volume2 className="h-8 w-8 text-purple-400" />
									<div>
										<p className="text-2xl font-bold text-white">
											{Math.floor(consumptionStats.total_listening_time_seconds / 3600)}h {Math.floor((consumptionStats.total_listening_time_seconds % 3600) / 60)}m
										</p>
										<p className="text-sm text-gray-400">Audio Playback</p>
									</div>
								</div>
							</div>
							<div className="bg-gradient-to-br from-pink-500/10 to-rose-500/10 rounded-lg p-4">
								<div className="flex items-center space-x-3">
									<Mic className="h-8 w-8 text-pink-400" />
									<div>
										<p className="text-2xl font-bold text-white">
											{Math.floor(consumptionStats.total_ai_narration_time_seconds / 3600)}h {Math.floor((consumptionStats.total_ai_narration_time_seconds % 3600) / 60)}m
										</p>
										<p className="text-sm text-gray-400">AI Narration</p>
									</div>
								</div>
							</div>
							<div className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-lg p-4">
								<div className="flex items-center space-x-3">
									<Clock className="h-8 w-8 text-amber-400" />
									<div>
										<p className="text-2xl font-bold text-white">
											{consumptionStats.average_session_minutes.toFixed(0)}m
										</p>
										<p className="text-sm text-gray-400">Avg Session</p>
									</div>
								</div>
							</div>
						</div>
					</motion.div>
				)}

				{/* Listening History Card */}
				{listeningHistory && (
					<motion.div
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ delay: 0.2 }}
						className="bg-gray-800 rounded-xl p-6"
					>
						<div className="flex items-center justify-between mb-6">
							<h3 className="text-xl font-semibold text-white flex items-center space-x-2">
								<BookOpen className="h-5 w-5 text-blue-400" />
								<span>Listening History</span>
							</h3>
							<div className="flex items-center gap-2">
								<span className="text-sm text-gray-400">
									{listeningHistory.total_books} books • {listeningHistory.total_listening_hours.toFixed(1)} hrs
								</span>
								<button
									onClick={() => loadListeningHistory()}
									className="text-sm text-gray-400 hover:text-white transition-colors"
									title="Refresh history"
								>
									Refresh
								</button>
							</div>
						</div>

						{loadingHistory ? (
							<div className="flex items-center justify-center py-10">
								<Loader className="animate-spin text-blue-500" size={32} />
							</div>
						) : listeningHistory.books.length === 0 ? (
							<div className="text-center py-10">
								<BookOpen size={48} className="text-gray-600 mx-auto mb-3" />
								<p className="text-gray-400">No listening history yet</p>
								<p className="text-sm text-gray-500 mt-2">Start listening to books to build your history</p>
							</div>
						) : (
							<>
								<div className="space-y-3">
									{(showAllBooks ? listeningHistory.books : listeningHistory.books.slice(0, 5)).map((book, index) => {
										const percentOfTotal = (book.listening_hours / listeningHistory.total_listening_hours) * 100;
										const lastListenedDate = book.last_listened ? new Date(book.last_listened) : null;
										const formattedDate = lastListenedDate
											? lastListenedDate.toLocaleDateString('en-US', {
													month: 'short',
													day: 'numeric',
													year: 'numeric',
											  })
											: 'Never';

										return (
											<motion.div
												key={book.book_id}
												initial={{ opacity: 0, x: -20 }}
												animate={{ opacity: 1, x: 0 }}
												transition={{ delay: index * 0.05 }}
												className="bg-gray-900/50 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors"
											>
												<div className="flex items-start justify-between gap-4 mb-3">
													<div className="flex-1 min-w-0">
														<h4 className="text-white font-medium truncate mb-1">
															{book.book_title}
														</h4>
														<div className="flex items-center gap-3 text-sm text-gray-400">
															<div className="flex items-center gap-1">
																<Clock size={14} />
																<span>{book.listening_hours.toFixed(1)} hrs</span>
															</div>
															<div className="flex items-center gap-1">
																<MessageCircle size={14} />
																<span>{book.session_count} sessions</span>
															</div>
															<div className="flex items-center gap-1">
																<Calendar className="h-3.5 w-3.5" />
																<span>{formattedDate}</span>
															</div>
														</div>
													</div>
												</div>

												{/* Progress Bar */}
												<div>
													<div className="w-full bg-gray-700 rounded-full h-1.5">
														<div
															className="bg-gradient-to-r from-blue-500 to-purple-500 h-1.5 rounded-full"
															style={{ width: `${Math.min(percentOfTotal, 100)}%` }}
														/>
													</div>
													<p className="text-xs text-gray-500 mt-1">
														{percentOfTotal.toFixed(1)}% of total listening time
													</p>
												</div>
											</motion.div>
										);
									})}
								</div>

								{listeningHistory.books.length > 5 && (
									<div className="mt-4 text-center">
										<button
											onClick={() => setShowAllBooks(!showAllBooks)}
											className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
										>
											{showAllBooks
												? 'Show Less'
												: `Show All ${listeningHistory.books.length} Books`}
										</button>
									</div>
								)}
							</>
						)}
					</motion.div>
				)}

				{/* Avatar Upload Modal */}
				{showAvatarModal && (
					<div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
						<motion.div
							initial={{ opacity: 0, scale: 0.95 }}
							animate={{ opacity: 1, scale: 1 }}
							className="bg-gray-800 rounded-2xl p-6 max-w-md w-full"
						>
							<h3 className="text-xl font-semibold text-white mb-4">Update Avatar</h3>

							<div className="space-y-4">
								{/* File Upload */}
								<div>
									<label className="text-sm text-gray-400 block mb-2">Upload Image</label>
									<input
										ref={fileInputRef}
										type="file"
										accept="image/*"
										onChange={handleAvatarFileUpload}
										className="hidden"
									/>
									<button
										onClick={() => fileInputRef.current?.click()}
										disabled={uploadingAvatar}
										className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-600 text-white rounded-lg transition"
									>
										<Upload className="h-5 w-5" />
										<span>Choose File</span>
									</button>
									<p className="text-xs text-gray-500 mt-1">JPG, PNG, WebP up to 5MB</p>
								</div>

								<div className="relative">
									<div className="absolute inset-0 flex items-center">
										<div className="w-full border-t border-gray-700"></div>
									</div>
									<div className="relative flex justify-center text-sm">
										<span className="px-2 bg-gray-800 text-gray-400">or</span>
									</div>
								</div>

								{/* URL Input */}
								<div>
									<label className="text-sm text-gray-400 block mb-2">Image URL</label>
									<div className="flex space-x-2">
										<input
											type="url"
											value={avatarUrlInput}
											onChange={(e) => setAvatarUrlInput(e.target.value)}
											placeholder="https://example.com/avatar.jpg"
											className="flex-1 bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
										/>
										<button
											onClick={handleAvatarUrlSubmit}
											disabled={uploadingAvatar || !avatarUrlInput.trim()}
											className="px-4 py-2 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-600 text-white rounded-lg transition"
										>
											{uploadingAvatar ? <Loader className="h-5 w-5 animate-spin" /> : <LinkIcon className="h-5 w-5" />}
										</button>
									</div>
								</div>
							</div>

							<div className="flex space-x-3 mt-6">
								<button
									onClick={() => setShowAvatarModal(false)}
									className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
								>
									Cancel
								</button>
							</div>
						</motion.div>
					</div>
				)}

				{/* Settings Sections */}
				<div className="grid grid-cols-1 gap-6">
					{/* Reading Preferences */}
					<motion.div
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ delay: 0.2 }}
						className="bg-gray-800 rounded-xl p-6"
					>
						<h3 className="text-xl font-semibold text-white mb-4 flex items-center space-x-2">
							<BookOpen className="h-5 w-5 text-purple-400" />
							<span>Reading Preferences</span>
						</h3>
						<div className="space-y-4">
							<div>
								<label className="text-white font-medium block mb-2">
									Reading Level
								</label>
								<select
									value={readingLevel}
									onChange={(e) => setReadingLevel(e.target.value)}
									className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
								>
									<option value="beginner">Beginner</option>
									<option value="intermediate">Intermediate</option>
									<option value="advanced">Advanced</option>
								</select>
								<p className="text-sm text-gray-400 mt-1">
									Adjusts explanation complexity to match your level
								</p>
							</div>

							<div>
								<label className="text-white font-medium block mb-2">
									Explanation Depth
								</label>
								<div className="flex space-x-4">
									<button
										onClick={() => setExplanationDepth('brief')}
										className={`flex-1 px-4 py-2 rounded-lg transition ${explanationDepth === 'brief'
											? 'bg-purple-500 text-white'
											: 'bg-gray-700 text-gray-300 hover:bg-gray-600'
											}`}
									>
										Brief
									</button>
									<button
										onClick={() => setExplanationDepth('detailed')}
										className={`flex-1 px-4 py-2 rounded-lg transition ${explanationDepth === 'detailed'
											? 'bg-purple-500 text-white'
											: 'bg-gray-700 text-gray-300 hover:bg-gray-600'
											}`}
									>
										Detailed
									</button>
								</div>
							</div>

							<div>
								<label className="text-white font-medium block mb-2">
									Discussion Topics
								</label>
								<div className="flex flex-wrap gap-2">
									{['themes', 'characters', 'context', 'symbolism', 'plot', 'setting'].map((topic) => (
										<button
											key={topic}
											onClick={() => handleTopicToggle(topic)}
											className={`px-4 py-2 rounded-lg transition capitalize ${discussionTopics.includes(topic)
												? 'bg-purple-500 text-white'
												: 'bg-gray-700 text-gray-300 hover:bg-gray-600'
												}`}
										>
											{discussionTopics.includes(topic) && (
												<Check className="h-4 w-4 inline mr-1" />
											)}
											{topic}
										</button>
									))}
								</div>
								<p className="text-sm text-gray-400 mt-2">
									Select topics you're interested in discussing
								</p>
							</div>
						</div>
					</motion.div>

					{/* Voice Settings */}
					<motion.div
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ delay: 0.3 }}
						className="bg-gray-800 rounded-xl p-6"
					>
						<h3 className="text-xl font-semibold text-white mb-4 flex items-center space-x-2">
							<Volume2 className="h-5 w-5 text-purple-400" />
							<span>Voice Preferences</span>
						</h3>
						<div className="space-y-4">
							<div>
								<div className="flex items-center justify-between mb-2">
									<label className="text-white font-medium">Playback Speed</label>
									<span className="text-purple-400 font-semibold">{playbackSpeed}x</span>
								</div>
								<input
									type="range"
									min="0.5"
									max="2"
									step="0.25"
									value={playbackSpeed}
									onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
									className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
								/>
								<div className="flex justify-between text-xs text-gray-500 mt-1">
									<span>0.5x</span>
									<span>1x</span>
									<span>1.5x</span>
									<span>2x</span>
								</div>
							</div>

							<div>
								<label className="text-white font-medium block mb-2">
									Voice Provider
								</label>
								<select
									value={voiceProvider}
									onChange={(e) => setVoiceProvider(e.target.value)}
									className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
								>
									<option value="coqui_xtts">Coqui XTTS (Multi-language)</option>
									<option value="openai">OpenAI TTS</option>
									<option value="elevenlabs">ElevenLabs (Premium)</option>
								</select>
							</div>

							<div>
								<label className="text-white font-medium block mb-2">
									Voice Selection
								</label>
								<select
									value={voiceId}
									onChange={(e) => setVoiceId(e.target.value)}
									className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
								>
									<option value="nova">Nova</option>
									<option value="alloy">Alloy</option>
									<option value="echo">Echo</option>
									<option value="fable">Fable</option>
									<option value="onyx">Onyx</option>
									<option value="shimmer">Shimmer</option>
								</select>
							</div>

							<div>
								<label className="text-white font-medium block mb-2">
									Language
								</label>
								<select
									value={language}
									onChange={(e) => setLanguage(e.target.value)}
									className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:border-purple-500 focus:outline-none"
								>
									<option value="en">English</option>
									<option value="es">Spanish</option>
									<option value="fr">French</option>
									<option value="de">German</option>
									<option value="it">Italian</option>
									<option value="pt">Portuguese</option>
									<option value="ar">Arabic</option>
									<option value="zh">Chinese</option>
									<option value="ja">Japanese</option>
									<option value="ko">Korean</option>
								</select>
							</div>
						</div>
					</motion.div>

					{/* Local UI Settings (not saved to backend) */}
					<motion.div
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ delay: 0.4 }}
						className="bg-gray-800 rounded-xl p-6"
					>
						<h3 className="text-xl font-semibold text-white mb-4 flex items-center space-x-2">
							<Bell className="h-5 w-5 text-purple-400" />
							<span>UI Settings (Local)</span>
						</h3>
						<div className="space-y-4">
							<div className="flex items-center justify-between">
								<div>
									<p className="text-white font-medium">Auto-play Next Chapter</p>
									<p className="text-sm text-gray-400">
										Automatically play the next chapter when one ends
									</p>
								</div>
								<button
									onClick={handleAutoPlayToggle}
									className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${autoPlay ? 'bg-purple-500' : 'bg-gray-700'
										}`}
								>
									<span
										className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${autoPlay ? 'translate-x-6' : 'translate-x-1'
											}`}
									/>
								</button>
							</div>

							<div className="flex items-center justify-between">
								<div>
									<p className="text-white font-medium">Push Notifications</p>
									<p className="text-sm text-gray-400">
										Get notified about new books and updates
									</p>
								</div>
								<button
									onClick={handleNotificationToggle}
									className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${notifications ? 'bg-purple-500' : 'bg-gray-700'
										}`}
								>
									<span
										className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${notifications ? 'translate-x-6' : 'translate-x-1'
											}`}
									/>
								</button>
							</div>
						</div>
					</motion.div>

					{/* PWA Cache Settings */}
					<motion.div
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ delay: 0.45 }}
					>
						<PWACacheSettings />
					</motion.div>

					{/* Account Actions */}
					<motion.div
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ delay: 0.5 }}
						className="bg-gray-800 rounded-xl p-6"
					>
						<h3 className="text-xl font-semibold text-white mb-4">Account</h3>
						<div className="space-y-3">
							<button
								onClick={handleSignOut}
								className="w-full flex items-center justify-between px-4 py-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition"
							>
								<div className="flex items-center space-x-3">
									<LogOut className="h-5 w-5" />
									<span className="font-medium">Sign Out</span>
								</div>
							</button>
						</div>
					</motion.div>
				</div>
			</div>
		</motion.div>
	);
}
