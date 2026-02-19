import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
	BookOpen,
	Users,
	FileText,
	TrendingUp,
	Settings,
	Shield,
	Bell,
	BarChart3,
	Activity,
	Eye,
	Heart,
	MessageSquare,
	Share2,
	Calendar,
	Download,
	ArrowUp,
	ArrowDown,
	Minus,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
	SidebarProvider,
	SidebarTrigger,
} from "@/components/ui/sidebar";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";

interface AnalyticsData {
	totalViews: number;
	viewsChange: number;
	totalLikes: number;
	likesChange: number;
	totalComments: number;
	commentsChange: number;
	totalShares: number;
	sharesChange: number;
	avgReadTime: number;
	engagementRate: number;
	topDevotionals: Array<{
		title: string;
		author: string;
		views: number;
		likes: number;
	}>;
	topAuthors: Array<{
		name: string;
		devotionals: number;
		totalViews: number;
	}>;
}


const TrendIndicator = ({ value }: { value: number }) => {
	if (value > 0) {
		return (
			<div className="flex items-center gap-1 text-green-500">
				<ArrowUp className="w-4 h-4" />
				<span className="text-sm font-medium">+{value.toFixed(1)}%</span>
			</div>
		);
	} else if (value < 0) {
		return (
			<div className="flex items-center gap-1 text-red-500">
				<ArrowDown className="w-4 h-4" />
				<span className="text-sm font-medium">{value.toFixed(1)}%</span>
			</div>
		);
	}
	return (
		<div className="flex items-center gap-1 text-muted-foreground">
			<Minus className="w-4 h-4" />
			<span className="text-sm font-medium">0%</span>
		</div>
	);
};

export default function AdminAnalytics() {
	const { toast } = useToast();
	const [loading, setLoading] = useState(true);
	const [timeRange, setTimeRange] = useState("30");
	const [analytics, setAnalytics] = useState<AnalyticsData>({
		totalViews: 152847,
		viewsChange: 12.5,
		totalLikes: 45892,
		likesChange: 8.3,
		totalComments: 12563,
		commentsChange: 15.7,
		totalShares: 8934,
		sharesChange: 6.2,
		avgReadTime: 4.2,
		engagementRate: 8.4,
		topDevotionals: [
			{ title: "Walking in Divine Purpose", author: "Pastor John", views: 12453, likes: 892 },
			{ title: "The Power of Prayer", author: "Rev. Sarah", views: 10234, likes: 756 },
			{ title: "Finding Peace in Chaos", author: "Pastor Michael", views: 9876, likes: 723 },
			{ title: "God's Unfailing Love", author: "Rev. Emily", views: 8543, likes: 654 },
			{ title: "Walking by Faith", author: "Pastor David", views: 7234, likes: 567 },
		],
		topAuthors: [
			{ name: "Pastor John Smith", devotionals: 156, totalViews: 234567 },
			{ name: "Rev. Sarah Johnson", devotionals: 142, totalViews: 198234 },
			{ name: "Pastor Michael Chen", devotionals: 128, totalViews: 176543 },
			{ name: "Rev. Emily Brown", devotionals: 115, totalViews: 154321 },
			{ name: "Pastor David Lee", devotionals: 98, totalViews: 134567 },
		],
	});

	useEffect(() => {
		loadAnalytics();
	}, [timeRange]);

	const loadAnalytics = async () => {
		setLoading(true);
		try {
			const [dashboardData, topDevotionalsData] = await Promise.all([
				apiClient.getAdminAnalytics(parseInt(timeRange)),
				apiClient.client.get('/analytics/devotionals/top', {
					params: { limit: 5, days: parseInt(timeRange), metric: 'views' }
				}).then(r => r.data).catch(() => []),
			]);

			if (dashboardData) {
				setAnalytics({
					totalViews: dashboardData.total_views || 0,
					viewsChange: dashboardData.views_change || 0,
					totalLikes: dashboardData.total_likes || 0,
					likesChange: dashboardData.likes_change || 0,
					totalComments: dashboardData.total_comments || 0,
					commentsChange: dashboardData.comments_change || 0,
					totalShares: dashboardData.total_shares || 0,
					sharesChange: dashboardData.shares_change || 0,
					avgReadTime: dashboardData.avg_read_time || 0,
					engagementRate: dashboardData.engagement_rate || 0,
					topDevotionals: (topDevotionalsData || []).map((d: any) => ({
						title: d.title || '',
						author: d.author_name || 'Unknown',
						views: d.views || 0,
						likes: d.likes || 0,
					})),
					topAuthors: [], // TODO: Add top authors endpoint or calculate from data
				});
			}
		} catch (error) {
			console.error('Failed to load analytics:', error);
			toast({
				title: "Error",
				description: "Failed to load analytics data",
				variant: "destructive",
			});
		} finally {
			setLoading(false);
		}
	};

	return (
		<SidebarProvider>
			<div className="flex min-h-screen w-full bg-background">
				<AdminSidebar />

				<main className="flex-1 overflow-auto">
					{/* Header */}
					<header className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
						<div className="flex h-16 items-center gap-4 px-6">
							<SidebarTrigger className="md:hidden" />
							<div className="flex-1">
								<h1 className="text-xl font-serif font-bold text-foreground">Platform Analytics</h1>
								<p className="text-sm text-muted-foreground">Comprehensive platform performance insights</p>
							</div>
							<Select value={timeRange} onValueChange={setTimeRange}>
								<SelectTrigger className="w-40">
									<SelectValue />
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="7">Last 7 days</SelectItem>
									<SelectItem value="30">Last 30 days</SelectItem>
									<SelectItem value="90">Last 90 days</SelectItem>
									<SelectItem value="365">Last year</SelectItem>
								</SelectContent>
							</Select>
							<Button variant="outline">
								<Download className="w-4 h-4 mr-2" />
								Export Report
							</Button>
						</div>
					</header>

					{/* Content */}
					<div className="p-6 space-y-6">
						{/* Key Metrics */}
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
							<motion.div
								initial={{ opacity: 0, y: 20 }}
								animate={{ opacity: 1, y: 0 }}
								className="bg-card rounded-xl border border-border p-6"
							>
								<div className="flex items-center justify-between mb-4">
									<div className="p-2 rounded-lg bg-blue-500/10">
										<Eye className="w-5 h-5 text-blue-500" />
									</div>
									<TrendIndicator value={analytics.viewsChange} />
								</div>
								<h3 className="text-2xl font-bold text-foreground">
									{analytics.totalViews.toLocaleString()}
								</h3>
								<p className="text-sm text-muted-foreground mt-1">Total Views</p>
							</motion.div>

							<motion.div
								initial={{ opacity: 0, y: 20 }}
								animate={{ opacity: 1, y: 0 }}
								transition={{ delay: 0.1 }}
								className="bg-card rounded-xl border border-border p-6"
							>
								<div className="flex items-center justify-between mb-4">
									<div className="p-2 rounded-lg bg-red-500/10">
										<Heart className="w-5 h-5 text-red-500" />
									</div>
									<TrendIndicator value={analytics.likesChange} />
								</div>
								<h3 className="text-2xl font-bold text-foreground">
									{analytics.totalLikes.toLocaleString()}
								</h3>
								<p className="text-sm text-muted-foreground mt-1">Total Likes</p>
							</motion.div>

							<motion.div
								initial={{ opacity: 0, y: 20 }}
								animate={{ opacity: 1, y: 0 }}
								transition={{ delay: 0.2 }}
								className="bg-card rounded-xl border border-border p-6"
							>
								<div className="flex items-center justify-between mb-4">
									<div className="p-2 rounded-lg bg-purple-500/10">
										<MessageSquare className="w-5 h-5 text-purple-500" />
									</div>
									<TrendIndicator value={analytics.commentsChange} />
								</div>
								<h3 className="text-2xl font-bold text-foreground">
									{analytics.totalComments.toLocaleString()}
								</h3>
								<p className="text-sm text-muted-foreground mt-1">Total Comments</p>
							</motion.div>

							<motion.div
								initial={{ opacity: 0, y: 20 }}
								animate={{ opacity: 1, y: 0 }}
								transition={{ delay: 0.3 }}
								className="bg-card rounded-xl border border-border p-6"
							>
								<div className="flex items-center justify-between mb-4">
									<div className="p-2 rounded-lg bg-green-500/10">
										<Share2 className="w-5 h-5 text-green-500" />
									</div>
									<TrendIndicator value={analytics.sharesChange} />
								</div>
								<h3 className="text-2xl font-bold text-foreground">
									{analytics.totalShares.toLocaleString()}
								</h3>
								<p className="text-sm text-muted-foreground mt-1">Total Shares</p>
							</motion.div>
						</div>

						{/* Engagement Metrics */}
						<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
							<Card>
								<CardHeader>
									<CardTitle>Engagement Overview</CardTitle>
									<CardDescription>Reader interaction metrics</CardDescription>
								</CardHeader>
								<CardContent className="space-y-4">
									<div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
										<span className="text-sm font-medium">Avg. Reading Time</span>
										<span className="text-lg font-bold">{analytics.avgReadTime} min</span>
									</div>
									<div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
										<span className="text-sm font-medium">Engagement Rate</span>
										<span className="text-lg font-bold">{analytics.engagementRate}%</span>
									</div>
									<div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
										<span className="text-sm font-medium">Comments per Devotional</span>
										<span className="text-lg font-bold">
											{(analytics.totalComments / analytics.topDevotionals.length).toFixed(1)}
										</span>
									</div>
									<div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
										<span className="text-sm font-medium">Likes per Devotional</span>
										<span className="text-lg font-bold">
											{(analytics.totalLikes / analytics.topDevotionals.length).toFixed(1)}
										</span>
									</div>
								</CardContent>
							</Card>

							<Card>
								<CardHeader>
									<CardTitle>Top Performing Devotionals</CardTitle>
									<CardDescription>Most viewed content this period</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="space-y-4">
										{analytics.topDevotionals.map((devotional, index) => (
											<div key={index} className="flex items-center gap-4">
												<div className="flex items-center justify-center w-8 h-8 rounded-full bg-secondary text-secondary-foreground font-bold text-sm">
													{index + 1}
												</div>
												<div className="flex-1 min-w-0">
													<p className="font-medium text-sm truncate">{devotional.title}</p>
													<p className="text-xs text-muted-foreground">{devotional.author}</p>
												</div>
												<div className="text-right">
													<p className="text-sm font-bold">{devotional.views.toLocaleString()}</p>
													<p className="text-xs text-muted-foreground flex items-center gap-1">
														<Heart className="w-3 h-3" />
														{devotional.likes.toLocaleString()}
													</p>
												</div>
											</div>
										))}
									</div>
								</CardContent>
							</Card>
						</div>

						{/* Top Authors */}
						<Card>
							<CardHeader>
								<CardTitle>Top Authors</CardTitle>
								<CardDescription>Most active and engaging content creators</CardDescription>
							</CardHeader>
							<CardContent>
								<div className="space-y-4">
									{analytics.topAuthors.map((author, index) => (
										<div key={index} className="flex items-center gap-4 p-4 rounded-lg bg-muted/50">
											<div className="flex items-center justify-center w-10 h-10 rounded-full bg-secondary text-secondary-foreground font-bold">
												{index + 1}
											</div>
											<div className="flex-1">
												<p className="font-medium">{author.name}</p>
												<p className="text-sm text-muted-foreground">
													{author.devotionals} devotionals
												</p>
											</div>
											<div className="text-right">
												<p className="font-bold text-lg">{author.totalViews.toLocaleString()}</p>
												<p className="text-sm text-muted-foreground">Total Views</p>
											</div>
										</div>
									))}
								</div>
							</CardContent>
						</Card>
					</div>
				</main>
			</div>
		</SidebarProvider>
	);
}
