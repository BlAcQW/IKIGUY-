import { useState, useEffect, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import {
	ArrowLeft,
	BookOpen,
	Calendar,
	Heart,
	Bookmark,
	Settings,
	LogOut,
	Edit,
	ChevronRight,
	Clock,
	Trophy,
	TrendingUp,
	Bell,
	Save,
	Lock,
	Eye,
	EyeOff,
	Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { devotionalDB } from '@/lib/db';
import { useAuth } from '@/contexts/AuthContext';
import { useOfflineSync } from '@/hooks/useOfflineSync';
import { useToast } from '@/hooks/use-toast';
import { subscribeToPushNotifications, unsubscribeFromPushNotifications, isSubscribedToPushNotifications } from '@/utils/pushNotifications';
import { ProfileEditDialog } from '@/components/profile/ProfileEditDialog';
import { PrivacySettingsDialog } from '@/components/profile/PrivacySettingsDialog';
import { ReadingSettingsSection } from '@/components/profile/ReadingSettingsSection';
import { logger } from '@/lib/logger';

interface BookmarkItem {
	id: string;  // Devotional ID
	title: string;
	excerpt: string;
	cover_image_url?: string;
	published_at: string;
	reading_time_minutes: number;
	categories: string[];
	created_at: string;  // When bookmark was created
}

interface HistoryItem {
	devotional_id: string;
	devotional_title?: string;
	author_name?: string;
	reading_progress: number;
	listening_progress: number;
	last_read_at: string;
	time_spent_seconds: number;
}

const Profile = () => {
	const navigate = useNavigate();
	const [searchParams] = useSearchParams();
	const [activeTab, setActiveTab] = useState<"gamification" | "history" | "bookmarks" | "settings">(
		(searchParams.get('tab') as "gamification" | "history" | "bookmarks" | "settings") || "gamification"
	);

	// Hooks must be called at the top, before any conditional logic
	const { user, logout, loading } = useAuth();
	const { isOnline } = useOfflineSync();
	const { toast } = useToast();

	// Redirect to auth if not logged in
	useEffect(() => {
		if (!loading && !user) {
			navigate('/auth');
		}
	}, [user, loading, navigate]);

	// Dialog states
	const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
	const [isPrivacyDialogOpen, setIsPrivacyDialogOpen] = useState(false);

	// Notification settings state
	const [notificationsEnabled, setNotificationsEnabled] = useState(true);
	const [reminderTime, setReminderTime] = useState("08:00");
	const [pushNotificationsEnabled, setPushNotificationsEnabled] = useState(false);
	const [emailNotificationsEnabled, setEmailNotificationsEnabled] = useState(true);
	const [savingNotifications, setSavingNotifications] = useState(false);
	const [frequencySettings, setFrequencySettings] = useState({
		daily_reminders: 1,
		new_devotionals: 3,
		announcements: 2,
		total_per_day: 5,
	});

	// Password change state
	const [passwordData, setPasswordData] = useState({
		currentPassword: "",
		newPassword: "",
		confirmPassword: "",
	});
	const [showPasswords, setShowPasswords] = useState({
		current: false,
		new: false,
		confirm: false,
	});
	const [changingPassword, setChangingPassword] = useState(false);

	// Load user notification preferences
	useEffect(() => {
		if (user && activeTab === 'settings') {
			// Load from user preferences
			const prefs = user.reading_preferences;
			if (prefs) {
				if (prefs.notification_time) {
					setReminderTime(prefs.notification_time);
				}
				if (prefs.notifications_enabled !== undefined) {
					setNotificationsEnabled(prefs.notifications_enabled);
				}
			}
			// Check push notification subscription
			(async () => {
				try {
					const isSubscribed = await isSubscribedToPushNotifications();
					setPushNotificationsEnabled(isSubscribed);

					// Load frequency settings
					const freqSettings = await apiClient.getNotificationFrequency();
					setFrequencySettings(freqSettings);
				} catch (error) {
					logger.error('Failed to load push notification settings:', error);
				}
			})();
		}
	}, [user, activeTab]);

	// Fetch gamification profile - ALWAYS fetch for stats display
	const { data: gamificationProfile, isLoading: gamificationLoading } = useQuery({
		queryKey: ['gamificationProfile'],
		queryFn: async () => {
			try {
				return await apiClient.getGamificationProfile();
			} catch (error) {
				logger.error('Failed to fetch gamification profile:', error);
				return null;
			}
		},
		enabled: !!user, // Always fetch when logged in for stats
	});

	// Fetch streak data - ALWAYS fetch for stats display
	const { data: streakData } = useQuery({
		queryKey: ['streak'],
		queryFn: async () => {
			try {
				return await apiClient.getStreak();
			} catch (error) {
				logger.error('Failed to fetch streak:', error);
				return null;
			}
		},
		enabled: !!user, // Always fetch when logged in for stats
	});

	// Fetch achievements
	const { data: achievements = [] } = useQuery({
		queryKey: ['achievements'],
		queryFn: async () => {
			try {
				return await apiClient.getAchievements();
			} catch (error) {
				logger.error('Failed to fetch achievements:', error);
				return [];
			}
		},
		enabled: activeTab === 'gamification' && !!user,
	});

	// Fetch bookmarks with offline fallback - ALWAYS fetch for stats
	const { data: bookmarks = [], isLoading: bookmarksLoading } = useQuery<BookmarkItem[]>({
		queryKey: ['bookmarks'],
		queryFn: async () => {
			try {
				const response = await apiClient.getBookmarkedDevotionals();
				logger.debug('📚 Bookmarks loaded:', response?.length || 0);
				// Backend returns array directly, not wrapped in { items: [] }
				return Array.isArray(response) ? response : [];
			} catch (error) {
				logger.error('Failed to fetch bookmarks:', error);
				if (!isOnline) {
					// Fallback to cached bookmarks
					const cached = await devotionalDB.getBookmarks();
					return cached as BookmarkItem[];
				}
				throw error;
			}
		},
		enabled: !!user, // Always fetch when logged in for stats
		staleTime: 0, // Always fetch fresh data
		gcTime: 0, // Don't cache (was cacheTime in v4)
	});

	// Fetch reading history with offline fallback - ALWAYS fetch for stats
	const { data: history = [], isLoading: historyLoading } = useQuery<HistoryItem[]>({
		queryKey: ['reading_history'],
		queryFn: async () => {
			try {
				const response = await apiClient.getReadingHistory();
				// Backend returns array directly, not wrapped in { items: [] }
				return response || [];
			} catch (error) {
				if (!isOnline) {
					// Fallback to cached history
					const cached = await devotionalDB.getReadingHistory();
					return cached as HistoryItem[];
				}
				throw error;
			}
		},
		enabled: !!user, // Always fetch when logged in for stats
	});

	const handleSignOut = async () => {
		try {
			await logout();
			toast({
				title: "Signed out",
				description: "You've been signed out successfully"
			});
			navigate("/auth");
		} catch (error) {
			logger.error('Logout error:', error);
			// Still navigate even if logout fails
			navigate("/auth");
		}
	};

	const formatDate = useCallback((dateString: string) => {
		const date = new Date(dateString);
		const now = new Date();
		const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

		if (diffInHours < 1) return "Just now";
		if (diffInHours < 24) return "Today";
		if (diffInHours < 48) return "Yesterday";

		const diffInDays = Math.floor(diffInHours / 24);
		if (diffInDays < 7) return `${diffInDays} days ago`;

		return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}, []);

	const formatReadingTime = useCallback((seconds: number) => {
		const minutes = Math.floor(seconds / 60);
		if (minutes < 1) return "< 1 min";
		if (minutes < 60) return `${minutes} min`;
		const hours = Math.floor(minutes / 60);
		const remainingMins = minutes % 60;
		return `${hours}h ${remainingMins}m`;
	}, []);

	const getAuthorInitials = useCallback((name: string | undefined) => {
		if (!name || typeof name !== 'string') return "?";
		return name
			.split(' ')
			.filter(n => n.length > 0)
			.map(n => n[0])
			.join('')
			.toUpperCase()
			.slice(0, 2) || "?";
	}, []);

	const getUserInitials = useMemo(() => {
		if (!user?.name) return "U";
		return getAuthorInitials(user.name);
	}, [user?.name, getAuthorInitials]);

	const getJoinedDate = useMemo(() => {
		if (!user) return "Member since 2024";
		// This would come from the user object created_at field
		return "Member since 2024";
	}, [user]);

	// Calculate stats - memoized to prevent recalculation
	const stats = useMemo(() => ({
		devotionalsRead: gamificationProfile?.total_devotionals_read || history.length,
		currentStreak: gamificationProfile?.current_streak || 0,
		bookmarked: bookmarks.length,
		currentLevel: gamificationProfile?.current_level || 1,
	}), [gamificationProfile, history.length, bookmarks.length]);

	// Show loading state while checking authentication
	if (loading) {
		return (
			<div className="min-h-screen bg-background flex items-center justify-center">
				<div className="text-center">
					<div className="w-16 h-16 border-4 border-secondary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
					<p className="text-muted-foreground">Loading profile...</p>
				</div>
			</div>
		);
	}

	// Don't render if not authenticated (will redirect)
	if (!user) {
		return null;
	}

	return (
		<div className="min-h-screen bg-background">
			{/* Header */}
			<header className="sticky top-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border">
				<div className="container mx-auto px-4">
					<div className="flex items-center justify-between h-14">
						<Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
							<ArrowLeft className="w-5 h-5" />
						</Button>
						<span className="font-serif font-semibold">Profile</span>
						<Button
							variant="ghost"
							size="icon"
							onClick={() => setActiveTab("settings")}
						>
							<Settings className="w-5 h-5" />
						</Button>
					</div>
				</div>
			</header>

			<main className="container mx-auto px-4 py-6 md:py-8">
				<div className="max-w-2xl mx-auto">
					<motion.div
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ duration: 0.5 }}
					>
						{/* Profile Card */}
						<div className="text-center mb-6 md:mb-8">
							<div className="w-20 h-20 md:w-24 md:h-24 rounded-full bg-secondary/20 flex items-center justify-center mx-auto mb-4">
								<span className="font-bold text-2xl md:text-3xl text-secondary">
									{getUserInitials()}
								</span>
							</div>
							<h1 className="font-serif text-xl md:text-2xl font-bold text-foreground mb-1">
								{user?.name || "User"}
							</h1>
							<p className="text-sm md:text-base text-muted-foreground mb-2">
								{user?.email || ""}
							</p>
							<p className="text-xs md:text-sm text-muted-foreground">
								{getJoinedDate()}
							</p>
							<Button
								variant="outline"
								size="sm"
								className="mt-4 gap-2"
								onClick={() => setIsEditDialogOpen(true)}
							>
								<Edit className="w-4 h-4" />
								Edit Profile
							</Button>
						</div>

						{/* Stats */}
						<div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-6 md:mb-8">
							<div className="bg-card rounded-2xl p-3 md:p-4 border border-border text-center">
								<div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-secondary/10 flex items-center justify-center mx-auto mb-2">
									<BookOpen className="w-4 h-4 md:w-5 md:h-5 text-secondary" />
								</div>
								<p className="font-serif text-xl md:text-2xl font-bold text-foreground">
									{stats.devotionalsRead}
								</p>
								<p className="text-xs md:text-sm text-muted-foreground">Devotionals</p>
							</div>
							<div className="bg-card rounded-2xl p-3 md:p-4 border border-border text-center">
								<div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-accent/10 flex items-center justify-center mx-auto mb-2">
									<Calendar className="w-4 h-4 md:w-5 md:h-5 text-accent" />
								</div>
								<p className="font-serif text-xl md:text-2xl font-bold text-foreground">
									{stats.currentStreak}
								</p>
								<p className="text-xs md:text-sm text-muted-foreground">Day Streak</p>
							</div>
							<div className="bg-card rounded-2xl p-3 md:p-4 border border-border text-center">
								<div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-secondary/10 flex items-center justify-center mx-auto mb-2">
									<Bookmark className="w-4 h-4 md:w-5 md:h-5 text-secondary" />
								</div>
								<p className="font-serif text-xl md:text-2xl font-bold text-foreground">
									{stats.bookmarked}
								</p>
								<p className="text-xs md:text-sm text-muted-foreground">Bookmarked</p>
							</div>
							<div className="bg-card rounded-2xl p-3 md:p-4 border border-border text-center">
								<div className="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-purple-500/10 flex items-center justify-center mx-auto mb-2">
									<Trophy className="w-4 h-4 md:w-5 md:h-5 text-purple-500" />
								</div>
								<p className="font-serif text-xl md:text-2xl font-bold text-foreground">
									{stats.currentLevel}
								</p>
								<p className="text-xs md:text-sm text-muted-foreground">Level</p>
							</div>
						</div>

						{/* Tabs */}
						<div className="flex gap-2 mb-6">
							<button
								onClick={() => setActiveTab("gamification")}
								className={`flex-1 py-2.5 md:py-3 rounded-xl font-medium text-sm md:text-base transition-colors ${activeTab === "gamification"
										? "bg-secondary text-secondary-foreground"
										: "bg-muted text-muted-foreground hover:bg-muted/80"
									}`}
							>
								<div className="flex items-center justify-center gap-1.5">
									<Trophy className="w-4 h-4" />
									<span>Progress</span>
								</div>
							</button>
							<button
								onClick={() => setActiveTab("history")}
								className={`flex-1 py-2.5 md:py-3 rounded-xl font-medium text-sm md:text-base transition-colors ${activeTab === "history"
										? "bg-secondary text-secondary-foreground"
										: "bg-muted text-muted-foreground hover:bg-muted/80"
									}`}
							>
								History
							</button>
							<button
								onClick={() => setActiveTab("bookmarks")}
								className={`flex-1 py-2.5 md:py-3 rounded-xl font-medium text-sm md:text-base transition-colors ${activeTab === "bookmarks"
										? "bg-secondary text-secondary-foreground"
										: "bg-muted text-muted-foreground hover:bg-muted/80"
									}`}
							>
								Saved
							</button>
							<button
								onClick={() => setActiveTab("settings")}
								className={`flex-1 py-2.5 md:py-3 rounded-xl font-medium text-sm md:text-base transition-colors ${activeTab === "settings"
										? "bg-secondary text-secondary-foreground"
										: "bg-muted text-muted-foreground hover:bg-muted/80"
									}`}
							>
								<div className="flex items-center justify-center gap-1.5">
									<Settings className="w-4 h-4" />
									<span className="hidden sm:inline">Settings</span>
								</div>
							</button>
						</div>

						{/* Content */}
						<div className="space-y-3">
							{/* Gamification Tab */}
							{activeTab === "gamification" && (
								<>
									{gamificationLoading ? (
										// Loading skeleton
										<div className="space-y-4">
											{[1, 2, 3].map((i) => (
												<div
													key={i}
													className="h-32 bg-card rounded-xl border border-border animate-pulse"
												/>
											))}
										</div>
									) : (
										<div className="space-y-4">
											{/* Streak & Level */}
											<div className="grid md:grid-cols-2 gap-4">
												{streakData && (
													<div className="bg-card rounded-xl p-4 border border-border">
														<div className="flex items-center gap-3 mb-3">
															<div className="w-12 h-12 rounded-full bg-secondary/10 flex items-center justify-center">
																<Calendar className="w-6 h-6 text-secondary" />
															</div>
															<div>
																<h3 className="font-semibold text-foreground">Reading Streak</h3>
																<p className="text-sm text-muted-foreground">
																	{streakData.current_streak} day{streakData.current_streak !== 1 ? 's' : ''}
																</p>
															</div>
														</div>
														<div className="space-y-2 text-sm">
															<div className="flex justify-between">
																<span className="text-muted-foreground">Longest</span>
																<span className="font-medium text-foreground">{streakData.longest_streak} days</span>
															</div>
															<div className="flex justify-between">
																<span className="text-muted-foreground">Total</span>
																<span className="font-medium text-foreground">{streakData.total_days_read} days</span>
															</div>
															{streakData.streak_freezes_available > 0 && (
																<div className="flex justify-between pt-2 border-t border-border">
																	<span className="text-muted-foreground">Freezes</span>
																	<span className="font-medium text-blue-500">
																		❄️ {streakData.streak_freezes_available}
																	</span>
																</div>
															)}
														</div>
													</div>
												)}

												{gamificationProfile && (
													<div className="bg-card rounded-xl p-4 border border-border">
														<div className="flex items-center gap-3 mb-3">
															<div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center">
																<TrendingUp className="w-6 h-6 text-purple-500" />
															</div>
															<div>
																<h3 className="font-semibold text-foreground">Level Progress</h3>
																<p className="text-sm text-muted-foreground">
																	{gamificationProfile.level_tier}
																</p>
															</div>
														</div>
														<div className="space-y-2">
															<div className="flex items-center justify-between text-sm">
																<span className="text-muted-foreground">Level {gamificationProfile.current_level}</span>
																<span className="font-medium text-foreground">
																	{gamificationProfile.total_xp} / {gamificationProfile.xp_to_next_level} XP
																</span>
															</div>
															<div className="w-full h-2 bg-muted rounded-full overflow-hidden">
																<div
																	className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-300"
																	style={{
																		width: `${(gamificationProfile.total_xp / gamificationProfile.xp_to_next_level) * 100}%`
																	}}
																/>
															</div>
														</div>
													</div>
												)}
											</div>

											{/* Achievements */}
											{achievements && achievements.length > 0 && (
												<div className="bg-card rounded-xl p-4 border border-border">
													<div className="flex items-center justify-between mb-4">
														<h3 className="font-semibold text-foreground">Achievements</h3>
														<span className="text-sm text-muted-foreground">
															{achievements.filter((a: any) => a.unlocked).length} / {achievements.length}
														</span>
													</div>
													<div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
														{achievements.slice(0, 6).map((achievement: any) => (
															<div
																key={achievement.id}
																className={`p-3 rounded-lg border ${achievement.unlocked
																		? 'border-secondary bg-secondary/5'
																		: 'border-border opacity-50'
																	}`}
															>
																<div className="text-2xl mb-2">{achievement.icon_name}</div>
																<div className="text-xs font-medium text-foreground truncate">
																	{achievement.name}
																</div>
																{!achievement.unlocked && achievement.progress_target > 1 && (
																	<div className="mt-2">
																		<div className="w-full h-1 bg-muted rounded-full overflow-hidden">
																			<div
																				className="h-full bg-secondary rounded-full"
																				style={{
																					width: `${(achievement.progress / achievement.progress_target) * 100}%`
																				}}
																			/>
																		</div>
																		<div className="text-xs text-muted-foreground mt-1">
																			{achievement.progress}/{achievement.progress_target}
																		</div>
																	</div>
																)}
															</div>
														))}
													</div>
													{achievements.length > 6 && (
														<Button
															variant="ghost"
															size="sm"
															className="w-full mt-3"
															onClick={() => navigate("/achievements")}
														>
															View All Achievements
														</Button>
													)}
												</div>
											)}

											{/* Stats Overview */}
											{gamificationProfile && (
												<div className="bg-card rounded-xl p-4 border border-border">
													<h3 className="font-semibold text-foreground mb-4">Activity Stats</h3>
													<div className="grid grid-cols-2 gap-4 text-sm">
														<div>
															<p className="text-muted-foreground mb-1">Devotionals Read</p>
															<p className="text-xl font-bold text-foreground">
																{gamificationProfile.total_devotionals_read}
															</p>
														</div>
														<div>
															<p className="text-muted-foreground mb-1">Manna Coins</p>
															<p className="text-xl font-bold text-yellow-500">
																{gamificationProfile.manna_coins} 🪙
															</p>
														</div>
													</div>
												</div>
											)}
										</div>
									)}
								</>
							)}

							{/* Reading History */}
							{activeTab === "history" && (
								<>
									{historyLoading ? (
										// Loading skeleton
										<div className="space-y-3">
											{[1, 2, 3].map((i) => (
												<div
													key={i}
													className="flex items-center gap-3 p-4 bg-card rounded-xl border border-border animate-pulse"
												>
													<div className="w-10 h-10 rounded-lg bg-muted shrink-0" />
													<div className="flex-1 space-y-2">
														<div className="h-4 w-3/4 bg-muted rounded" />
														<div className="h-3 w-1/2 bg-muted rounded" />
													</div>
												</div>
											))}
										</div>
									) : history.length === 0 ? (
										// Empty state
										<motion.div
											initial={{ opacity: 0, y: 20 }}
											animate={{ opacity: 1, y: 0 }}
											className="text-center py-12"
										>
											<div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
												<BookOpen className="w-8 h-8 text-muted-foreground" />
											</div>
											<h3 className="font-serif text-lg font-semibold text-foreground mb-2">
												No reading history yet
											</h3>
											<p className="text-muted-foreground mb-6">
												Start reading devotionals to see your history here
											</p>
											<Button
												variant="secondary"
												onClick={() => navigate("/feed")}
											>
												Browse Devotionals
											</Button>
										</motion.div>
									) : (
										history.map((item: HistoryItem, index) => (
											<motion.div
												key={item.devotional_id}
												initial={{ opacity: 0, x: -10 }}
												animate={{ opacity: 1, x: 0 }}
												transition={{ delay: index * 0.05 }}
												className="flex items-center gap-3 p-3 md:p-4 bg-card rounded-xl border border-border hover:shadow-soft transition-shadow cursor-pointer"
												onClick={() => navigate(`/devotional/${item.devotional_id}`)}
											>
												<div className="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center shrink-0">
													<BookOpen className="w-5 h-5 text-secondary" />
												</div>
												<div className="flex-1 min-w-0">
													<h3 className="font-medium text-sm md:text-base text-foreground truncate">
														{item.devotional_title || "Untitled Devotional"}
													</h3>
													<div className="flex items-center gap-2 text-xs md:text-sm text-muted-foreground flex-wrap">
														<span>{item.author_name || "Unknown Author"}</span>
														<span>•</span>
														<span>{formatDate(item.last_read_at)}</span>
														{item.time_spent_seconds > 0 && (
															<>
																<span>•</span>
																<span className="flex items-center gap-1">
																	<Clock className="w-3 h-3" />
																	{formatReadingTime(item.time_spent_seconds)}
																</span>
															</>
														)}
													</div>
													{item.reading_progress > 0 && item.reading_progress < 100 && (
														<div className="mt-2">
															<div className="h-1.5 bg-muted rounded-full overflow-hidden">
																<div
																	className="h-full bg-secondary rounded-full transition-all"
																	style={{ width: `${item.reading_progress}%` }}
																/>
															</div>
														</div>
													)}
												</div>
												<ChevronRight className="w-5 h-5 text-muted-foreground shrink-0" />
											</motion.div>
										))
									)}
								</>
							)}

							{/* Bookmarks */}
							{activeTab === "bookmarks" && (
								<>
									{bookmarksLoading ? (
										// Loading skeleton
										<div className="space-y-3">
											{[1, 2, 3].map((i) => (
												<div
													key={i}
													className="flex items-center gap-3 p-4 bg-card rounded-xl border border-border animate-pulse"
												>
													<div className="w-10 h-10 rounded-lg bg-muted shrink-0" />
													<div className="flex-1 space-y-2">
														<div className="h-4 w-3/4 bg-muted rounded" />
														<div className="h-3 w-1/2 bg-muted rounded" />
													</div>
												</div>
											))}
										</div>
									) : bookmarks.length === 0 ? (
										// Empty state
										<motion.div
											initial={{ opacity: 0, y: 20 }}
											animate={{ opacity: 1, y: 0 }}
											className="text-center py-12"
										>
											<div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
												<Bookmark className="w-8 h-8 text-muted-foreground" />
											</div>
											<h3 className="font-serif text-lg font-semibold text-foreground mb-2">
												No bookmarks yet
											</h3>
											<p className="text-muted-foreground mb-6">
												Bookmark devotionals to save them for later
											</p>
											<Button
												variant="secondary"
												onClick={() => navigate("/feed")}
											>
												Browse Devotionals
											</Button>
										</motion.div>
									) : (
										bookmarks.map((item: BookmarkItem, index) => (
											<motion.div
												key={item.id}
												initial={{ opacity: 0, x: -10 }}
												animate={{ opacity: 1, x: 0 }}
												transition={{ delay: index * 0.05 }}
												className="flex items-center gap-3 p-3 md:p-4 bg-card rounded-xl border border-border hover:shadow-soft transition-shadow cursor-pointer"
												onClick={() => navigate(`/devotional/${item.id}`)}
											>
												{item.cover_image_url ? (
													<div className="w-12 h-12 md:w-16 md:h-16 rounded-lg overflow-hidden shrink-0">
														<img
															src={item.cover_image_url}
															alt={item.title}
															className="w-full h-full object-cover"
														/>
													</div>
												) : (
													<div className="w-12 h-12 md:w-16 md:h-16 rounded-lg bg-secondary/10 flex items-center justify-center shrink-0">
														<Bookmark className="w-6 h-6 md:w-7 md:h-7 text-secondary" />
													</div>
												)}
												<div className="flex-1 min-w-0">
													<h3 className="font-medium text-sm md:text-base text-foreground truncate">
														{item.title}
													</h3>
													<p className="text-xs md:text-sm text-muted-foreground line-clamp-1">
														{item.excerpt}
													</p>
													<div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
														<span>{item.reading_time_minutes} min read</span>
														{item.categories && item.categories[0] && (
															<>
																<span>•</span>
																<span>{item.categories[0]}</span>
															</>
														)}
													</div>
												</div>
												<ChevronRight className="w-5 h-5 text-muted-foreground shrink-0" />
											</motion.div>
										))
									)}
								</>
							)}

							{/* Settings Tab */}
							{activeTab === "settings" && (
								<div className="space-y-4">
									{/* Daily Reminder Settings */}
									<div className="bg-card rounded-xl p-4 md:p-6 border border-border">
										<div className="flex items-center gap-3 mb-4">
											<div className="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center">
												<Bell className="w-5 h-5 text-secondary" />
											</div>
											<div>
												<h3 className="font-semibold text-foreground">Daily Reminders</h3>
												<p className="text-sm text-muted-foreground">
													Get notified to read your daily devotional
												</p>
											</div>
										</div>

										<div className="space-y-4">
											{/* Enable Notifications */}
											<div className="flex items-center justify-between">
												<div className="space-y-0.5">
													<Label htmlFor="notifications-enabled">Enable Daily Reminders</Label>
													<p className="text-sm text-muted-foreground">
														Receive daily notifications to read devotionals
													</p>
												</div>
												<Switch
													id="notifications-enabled"
													checked={notificationsEnabled}
													onCheckedChange={setNotificationsEnabled}
												/>
											</div>

											{/* Reminder Time */}
											{notificationsEnabled && (
												<div className="space-y-2">
													<Label htmlFor="reminder-time">Reminder Time</Label>
													<div className="flex items-center gap-2">
														<Input
															id="reminder-time"
															type="time"
															value={reminderTime}
															onChange={(e) => setReminderTime(e.target.value)}
															className="max-w-[150px]"
														/>
														<span className="text-sm text-muted-foreground">
															{new Date(`2000-01-01T${reminderTime}`).toLocaleTimeString('en-US', {
																hour: 'numeric',
																minute: '2-digit',
																hour12: true
															})}
														</span>
													</div>
													<p className="text-xs text-muted-foreground">
														Choose when you'd like to receive your daily reminder
													</p>
												</div>
											)}

											{/* Push Notifications */}
											<div className="flex items-center justify-between pt-2 border-t border-border">
												<div className="space-y-0.5">
													<Label htmlFor="push-notifications">Browser Notifications</Label>
													<p className="text-sm text-muted-foreground">
														Receive push notifications in your browser
													</p>
												</div>
												<Switch
													id="push-notifications"
													checked={pushNotificationsEnabled}
													onCheckedChange={async (checked) => {
														try {
															if (checked) {
																const success = await subscribeToPushNotifications();
																if (success) {
																	setPushNotificationsEnabled(true);
																	toast({
																		title: "Push notifications enabled",
																		description: "You'll receive notifications in your browser",
																	});
																} else {
																	setPushNotificationsEnabled(false);
																	toast({
																		title: "Permission denied",
																		description: "Please enable notifications in your browser settings",
																		variant: "destructive",
																	});
																}
															} else {
																await unsubscribeFromPushNotifications();
																setPushNotificationsEnabled(false);
																toast({
																	title: "Push notifications disabled",
																	description: "You won't receive browser notifications",
																});
															}
														} catch (error) {
															logger.error('Failed to toggle push notifications:', error);
															toast({
																title: "Error",
																description: "Failed to update push notification settings",
																variant: "destructive",
															});
														}
													}}
												/>
											</div>

											{/* Email Notifications */}
											<div className="flex items-center justify-between">
												<div className="space-y-0.5">
													<Label htmlFor="email-notifications">Email Notifications</Label>
													<p className="text-sm text-muted-foreground">
														Receive daily devotional reminders via email
													</p>
												</div>
												<Switch
													id="email-notifications"
													checked={emailNotificationsEnabled}
													onCheckedChange={setEmailNotificationsEnabled}
												/>
											</div>

											{/* Notification Frequency */}
											<div className="pt-4 border-t border-border space-y-4">
												<div>
													<Label className="text-base font-semibold">Notification Frequency</Label>
													<p className="text-sm text-muted-foreground">
														Control how many notifications you receive per day
													</p>
												</div>

												<div className="grid grid-cols-2 gap-3">
													<div className="space-y-2">
														<Label htmlFor="daily-reminders-freq" className="text-sm">
															Daily Reminders
														</Label>
														<Input
															id="daily-reminders-freq"
															type="number"
															min="0"
															max="3"
															value={frequencySettings.daily_reminders}
															onChange={(e) => setFrequencySettings(prev => ({
																...prev,
																daily_reminders: parseInt(e.target.value) || 0
															}))}
														/>
													</div>

													<div className="space-y-2">
														<Label htmlFor="new-devotionals-freq" className="text-sm">
															New Devotionals
														</Label>
														<Input
															id="new-devotionals-freq"
															type="number"
															min="0"
															max="10"
															value={frequencySettings.new_devotionals}
															onChange={(e) => setFrequencySettings(prev => ({
																...prev,
																new_devotionals: parseInt(e.target.value) || 0
															}))}
														/>
													</div>

													<div className="space-y-2">
														<Label htmlFor="announcements-freq" className="text-sm">
															Announcements
														</Label>
														<Input
															id="announcements-freq"
															type="number"
															min="0"
															max="5"
															value={frequencySettings.announcements}
															onChange={(e) => setFrequencySettings(prev => ({
																...prev,
																announcements: parseInt(e.target.value) || 0
															}))}
														/>
													</div>

													<div className="space-y-2">
														<Label htmlFor="total-freq" className="text-sm">
															Total Per Day
														</Label>
														<Input
															id="total-freq"
															type="number"
															min="0"
															max="20"
															value={frequencySettings.total_per_day}
															onChange={(e) => setFrequencySettings(prev => ({
																...prev,
																total_per_day: parseInt(e.target.value) || 0
															}))}
														/>
													</div>
												</div>
											</div>

											{/* Save Button */}
											<Button
												onClick={async () => {
													setSavingNotifications(true);
													try {
														if (notificationsEnabled) {
															await apiClient.scheduleDailyReminder(reminderTime);
														}

														// Save frequency settings
														await apiClient.updateNotificationFrequency(frequencySettings);

														toast({
															title: "Settings saved",
															description: "Your notification preferences have been updated",
														});
													} catch (error) {
														logger.error('Failed to save notification settings:', error);
														toast({
															title: "Error",
															description: "Failed to save notification settings",
															variant: "destructive"
														});
													} finally {
														setSavingNotifications(false);
													}
												}}
												disabled={savingNotifications}
												className="w-full gap-2"
											>
												<Save className="w-4 h-4" />
												{savingNotifications ? "Saving..." : "Save Preferences"}
											</Button>
										</div>
									</div>

									{/* Reading Settings */}
									<ReadingSettingsSection />

									{/* Password Change */}
									<div className="bg-card rounded-xl p-4 md:p-6 border border-border">
										<div className="flex items-center gap-3 mb-4">
											<div className="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center">
												<Lock className="w-5 h-5 text-secondary" />
											</div>
											<div>
												<h3 className="font-semibold text-foreground">Change Password</h3>
												<p className="text-sm text-muted-foreground">
													Update your account password
												</p>
											</div>
										</div>

										<div className="space-y-4">
											{/* Current Password */}
											<div className="space-y-2">
												<Label htmlFor="current-password">Current Password</Label>
												<div className="relative">
													<Input
														id="current-password"
														type={showPasswords.current ? "text" : "password"}
														value={passwordData.currentPassword}
														onChange={(e) =>
															setPasswordData({ ...passwordData, currentPassword: e.target.value })
														}
														placeholder="Enter current password"
														className="pr-10"
													/>
													<button
														type="button"
														onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
														className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
													>
														{showPasswords.current ? (
															<EyeOff className="w-4 h-4" />
														) : (
															<Eye className="w-4 h-4" />
														)}
													</button>
												</div>
											</div>

											{/* New Password */}
											<div className="space-y-2">
												<Label htmlFor="new-password">New Password</Label>
												<div className="relative">
													<Input
														id="new-password"
														type={showPasswords.new ? "text" : "password"}
														value={passwordData.newPassword}
														onChange={(e) =>
															setPasswordData({ ...passwordData, newPassword: e.target.value })
														}
														placeholder="Enter new password"
														className="pr-10"
													/>
													<button
														type="button"
														onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
														className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
													>
														{showPasswords.new ? (
															<EyeOff className="w-4 h-4" />
														) : (
															<Eye className="w-4 h-4" />
														)}
													</button>
												</div>
												<p className="text-xs text-muted-foreground">
													Must be at least 8 characters with uppercase, lowercase, and a number
												</p>
											</div>

											{/* Confirm Password */}
											<div className="space-y-2">
												<Label htmlFor="confirm-password">Confirm New Password</Label>
												<div className="relative">
													<Input
														id="confirm-password"
														type={showPasswords.confirm ? "text" : "password"}
														value={passwordData.confirmPassword}
														onChange={(e) =>
															setPasswordData({ ...passwordData, confirmPassword: e.target.value })
														}
														placeholder="Confirm new password"
														className="pr-10"
													/>
													<button
														type="button"
														onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
														className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
													>
														{showPasswords.confirm ? (
															<EyeOff className="w-4 h-4" />
														) : (
															<Eye className="w-4 h-4" />
														)}
													</button>
												</div>
											</div>

											{/* Change Password Button */}
											<Button
												onClick={async () => {
													// Validate
													if (!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
														toast({
															title: "All fields required",
															description: "Please fill in all password fields",
															variant: "destructive",
														});
														return;
													}

													if (passwordData.newPassword !== passwordData.confirmPassword) {
														toast({
															title: "Passwords don't match",
															description: "New password and confirmation must match",
															variant: "destructive",
														});
														return;
													}

													if (passwordData.newPassword.length < 8) {
														toast({
															title: "Password too short",
															description: "Password must be at least 8 characters long",
															variant: "destructive",
														});
														return;
													}

													setChangingPassword(true);
													try {
														await apiClient.changePassword(passwordData.currentPassword, passwordData.newPassword);
														toast({
															title: "Password changed",
															description: "Your password has been updated successfully",
														});
														setPasswordData({
															currentPassword: "",
															newPassword: "",
															confirmPassword: "",
														});
													} catch (error: any) {
														logger.error('Password change failed:', error);
														toast({
															title: "Password change failed",
															description: error.response?.data?.detail || "Failed to change password. Please check your current password.",
															variant: "destructive",
														});
													} finally {
														setChangingPassword(false);
													}
												}}
												disabled={changingPassword}
												className="w-full"
											>
												{changingPassword ? (
													<>
														<Loader2 className="w-4 h-4 mr-2 animate-spin" />
														Changing Password...
													</>
												) : (
													<>
														<Lock className="w-4 h-4 mr-2" />
														Change Password
													</>
												)}
											</Button>
										</div>
									</div>

									{/* Account Settings */}
									<div className="bg-card rounded-xl p-4 md:p-6 border border-border">
										<h3 className="font-semibold text-foreground mb-4">Account</h3>
										<div className="space-y-3">
											<Button
												variant="outline"
												className="w-full justify-between"
												onClick={() => setIsEditDialogOpen(true)}
											>
												<span>Edit Profile</span>
												<ChevronRight className="w-4 h-4" />
											</Button>
											<Button
												variant="outline"
												className="w-full justify-between"
												onClick={() => setIsPrivacyDialogOpen(true)}
											>
												<span>Privacy Settings</span>
												<ChevronRight className="w-4 h-4" />
											</Button>
										</div>
									</div>
								</div>
							)}
						</div>

						{/* Sign Out */}
						<Button
							variant="ghost"
							className="w-full mt-8 text-destructive hover:text-destructive hover:bg-destructive/10"
							onClick={handleSignOut}
						>
							<LogOut className="w-4 h-4 mr-2" />
							Sign Out
						</Button>
					</motion.div>
				</div>
			</main>

			{/* Profile Edit Dialog */}
			<ProfileEditDialog
				open={isEditDialogOpen}
				onOpenChange={setIsEditDialogOpen}
			/>

			{/* Privacy Settings Dialog */}
			<PrivacySettingsDialog
				open={isPrivacyDialogOpen}
				onOpenChange={setIsPrivacyDialogOpen}
			/>

			{/* Bottom Navigation */}
		</div>
	);
};

// Helper function to convert VAPID key
// urlBase64ToUint8Array moved to pushNotifications utility

export default Profile;
