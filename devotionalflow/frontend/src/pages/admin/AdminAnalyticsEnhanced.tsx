import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
	BookOpen,
	Users,
	FileText,
	TrendingUp,
	Eye,
	Heart,
	MessageSquare,
	Share2,
	Calendar,
	Download,
	ArrowUp,
	ArrowDown,
	Minus,
	Smartphone,
	Monitor,
	Tablet,
	Clock,
	MapPin,
	Link as LinkIcon,
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
import { Skeleton } from "@/components/ui/skeleton";

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

export default function AdminAnalyticsEnhanced() {
	const { toast } = useToast();
	const [loading, setLoading] = useState(true);
	const [timeRange, setTimeRange] = useState("30");
	
	// Dashboard stats
	const [dashboard, setDashboard] = useState<any>(null);
	const [trends, setTrends] = useState<any>(null);
	const [topDevotionals, setTopDevotionals] = useState<any[]>([]);
	const [insights, setInsights] = useState<any>(null);
	const [growth, setGrowth] = useState<any>(null);

	useEffect(() => {
		loadAnalytics();
	}, [timeRange]);

	const loadAnalytics = async () => {
		setLoading(true);
		try {
			const days = parseInt(timeRange);
			const [dashboardData, trendsData, topData, insightsData, growthData] = await Promise.all([
				apiClient.getDashboardAnalytics(days),
				apiClient.getEngagementTrends(days, 'daily'),
				apiClient.getTopDevotionals(10, 'views', days),
				apiClient.getReaderInsights(days),
				apiClient.getAudienceGrowth(Math.max(days, 90)),
			]);

			setDashboard(dashboardData);
			setTrends(trendsData);
			setTopDevotionals(topData);
			setInsights(insightsData);
			setGrowth(growthData);
		} catch (error: any) {
			console.error('Failed to load analytics:', error);
			toast({
				title: "Error",
				description: error.response?.data?.detail || "Failed to load analytics data",
				variant: "destructive",
			});
		} finally {
			setLoading(false);
		}
	};

	const handleExportCSV = async () => {
		try {
			const days = parseInt(timeRange);
			const blob = await apiClient.exportAnalyticsCSV(days);
			
			// Create download link
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `analytics_export_${days}days.csv`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			window.URL.revokeObjectURL(url);

			toast({
				title: "Export Successful",
				description: "Analytics data has been exported to CSV",
			});
		} catch (error: any) {
			console.error('Failed to export:', error);
			toast({
				title: "Export Failed",
				description: error.response?.data?.detail || "Failed to export analytics data",
				variant: "destructive",
			});
		}
	};

	const getDeviceIcon = (device: string) => {
		const lower = device.toLowerCase();
		if (lower.includes('mobile') || lower.includes('phone')) return Smartphone;
		if (lower.includes('tablet')) return Tablet;
		return Monitor;
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
								<h1 className="text-xl font-serif font-bold text-foreground">Analytics & Insights</h1>
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
							<Button variant="outline" onClick={handleExportCSV} disabled={loading}>
								<Download className="w-4 h-4 mr-2" />
								Export CSV
							</Button>
						</div>
					</header>

					{/* Content */}
					<div className="p-6 space-y-6">
						{/* Key Metrics */}
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
							{loading ? (
								Array.from({ length: 4 }).map((_, i) => (
									<Card key={i}>
										<CardContent className="p-6">
											<Skeleton className="h-8 w-24 mb-2" />
											<Skeleton className="h-4 w-16" />
										</CardContent>
									</Card>
								))
							) : dashboard ? (
								<>
									<motion.div
										initial={{ opacity: 0, y: 20 }}
										animate={{ opacity: 1, y: 0 }}
										className="bg-card rounded-xl border border-border p-6"
									>
										<div className="flex items-center justify-between mb-4">
											<div className="p-2 rounded-lg bg-blue-500/10">
												<Users className="w-5 h-5 text-blue-500" />
											</div>
											<TrendIndicator value={dashboard.readers_change} />
										</div>
										<h3 className="text-2xl font-bold text-foreground">
											{dashboard.total_readers.toLocaleString()}
										</h3>
										<p className="text-sm text-muted-foreground mt-1">Total Readers</p>
									</motion.div>

									<motion.div
										initial={{ opacity: 0, y: 20 }}
										animate={{ opacity: 1, y: 0 }}
										transition={{ delay: 0.1 }}
										className="bg-card rounded-xl border border-border p-6"
									>
										<div className="flex items-center justify-between mb-4">
											<div className="p-2 rounded-lg bg-purple-500/10">
												<FileText className="w-5 h-5 text-purple-500" />
											</div>
											<TrendIndicator value={dashboard.published_change} />
										</div>
										<h3 className="text-2xl font-bold text-foreground">
											{dashboard.devotionals_published.toLocaleString()}
										</h3>
										<p className="text-sm text-muted-foreground mt-1">Devotionals Published</p>
									</motion.div>

									<motion.div
										initial={{ opacity: 0, y: 20 }}
										animate={{ opacity: 1, y: 0 }}
										transition={{ delay: 0.2 }}
										className="bg-card rounded-xl border border-border p-6"
									>
										<div className="flex items-center justify-between mb-4">
											<div className="p-2 rounded-lg bg-green-500/10">
												<TrendingUp className="w-5 h-5 text-green-500" />
											</div>
										</div>
										<h3 className="text-2xl font-bold text-foreground">
											{dashboard.engagement_rate.toFixed(1)}%
										</h3>
										<p className="text-sm text-muted-foreground mt-1">Engagement Rate</p>
									</motion.div>

									<motion.div
										initial={{ opacity: 0, y: 20 }}
										animate={{ opacity: 1, y: 0 }}
										transition={{ delay: 0.3 }}
										className="bg-card rounded-xl border border-border p-6"
									>
										<div className="flex items-center justify-between mb-4">
											<div className="p-2 rounded-lg bg-blue-500/10">
												<Eye className="w-5 h-5 text-blue-500" />
											</div>
											<TrendIndicator value={dashboard.views_change} />
										</div>
										<h3 className="text-2xl font-bold text-foreground">
											{dashboard.total_views.toLocaleString()}
										</h3>
										<p className="text-sm text-muted-foreground mt-1">Total Views</p>
									</motion.div>
								</>
							) : null}
						</div>

						{/* Engagement Metrics */}
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
							{loading ? (
								Array.from({ length: 4 }).map((_, i) => (
									<Card key={i}>
										<CardContent className="p-6">
											<Skeleton className="h-8 w-24 mb-2" />
											<Skeleton className="h-4 w-16" />
										</CardContent>
									</Card>
								))
							) : dashboard ? (
								<>
									<Card>
										<CardContent className="p-6">
											<div className="flex items-center justify-between mb-4">
												<div className="p-2 rounded-lg bg-red-500/10">
													<Heart className="w-5 h-5 text-red-500" />
												</div>
												<TrendIndicator value={dashboard.likes_change} />
											</div>
											<h3 className="text-2xl font-bold text-foreground">
												{dashboard.total_likes.toLocaleString()}
											</h3>
											<p className="text-sm text-muted-foreground mt-1">Total Likes</p>
										</CardContent>
									</Card>

									<Card>
										<CardContent className="p-6">
											<div className="flex items-center justify-between mb-4">
												<div className="p-2 rounded-lg bg-purple-500/10">
													<MessageSquare className="w-5 h-5 text-purple-500" />
												</div>
												<TrendIndicator value={dashboard.comments_change} />
											</div>
											<h3 className="text-2xl font-bold text-foreground">
												{dashboard.total_comments.toLocaleString()}
											</h3>
											<p className="text-sm text-muted-foreground mt-1">Total Comments</p>
										</CardContent>
									</Card>

									<Card>
										<CardContent className="p-6">
											<div className="flex items-center justify-between mb-4">
												<div className="p-2 rounded-lg bg-green-500/10">
													<Share2 className="w-5 h-5 text-green-500" />
												</div>
												<TrendIndicator value={dashboard.shares_change} />
											</div>
											<h3 className="text-2xl font-bold text-foreground">
												{dashboard.total_shares.toLocaleString()}
											</h3>
											<p className="text-sm text-muted-foreground mt-1">Total Shares</p>
										</CardContent>
									</Card>

									<Card>
										<CardContent className="p-6">
											<div className="flex items-center justify-between mb-4">
												<div className="p-2 rounded-lg bg-secondary/10">
													<Clock className="w-5 h-5 text-secondary" />
												</div>
											</div>
											<h3 className="text-2xl font-bold text-foreground">
												{dashboard.avg_read_time.toFixed(1)} min
											</h3>
											<p className="text-sm text-muted-foreground mt-1">Avg Read Time</p>
										</CardContent>
									</Card>
								</>
							) : null}
						</div>

						{/* Engagement Trends Chart */}
						{trends && trends.trends && trends.trends.length > 0 && (
							<Card>
								<CardHeader>
									<CardTitle>Engagement Trends</CardTitle>
									<CardDescription>Views, likes, comments, and shares over time</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="h-64 overflow-x-auto">
										<div className="min-w-full space-y-2">
											{trends.trends.slice(-14).map((trend: any, index: number) => {
												const maxValue = Math.max(
													trend.views,
													trend.likes,
													trend.comments,
													trend.shares
												);
												return (
													<div key={index} className="flex items-center gap-2">
														<div className="w-24 text-xs text-muted-foreground">
															{new Date(trend.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
														</div>
														<div className="flex-1 flex gap-1">
															<div
																className="bg-blue-500 rounded"
																style={{ width: `${(trend.views / maxValue) * 100}%`, height: '20px' }}
																title={`Views: ${trend.views}`}
															/>
															<div
																className="bg-red-500 rounded"
																style={{ width: `${(trend.likes / maxValue) * 100}%`, height: '20px' }}
																title={`Likes: ${trend.likes}`}
															/>
															<div
																className="bg-purple-500 rounded"
																style={{ width: `${(trend.comments / maxValue) * 100}%`, height: '20px' }}
																title={`Comments: ${trend.comments}`}
															/>
															<div
																className="bg-green-500 rounded"
																style={{ width: `${(trend.shares / maxValue) * 100}%`, height: '20px' }}
																title={`Shares: ${trend.shares}`}
															/>
														</div>
													</div>
												);
											})}
										</div>
									</div>
									<div className="flex items-center gap-4 mt-4 text-sm">
										<div className="flex items-center gap-2">
											<div className="w-4 h-4 rounded bg-blue-500" />
											<span className="text-muted-foreground">Views</span>
										</div>
										<div className="flex items-center gap-2">
											<div className="w-4 h-4 rounded bg-red-500" />
											<span className="text-muted-foreground">Likes</span>
										</div>
										<div className="flex items-center gap-2">
											<div className="w-4 h-4 rounded bg-purple-500" />
											<span className="text-muted-foreground">Comments</span>
										</div>
										<div className="flex items-center gap-2">
											<div className="w-4 h-4 rounded bg-green-500" />
											<span className="text-muted-foreground">Shares</span>
										</div>
									</div>
								</CardContent>
							</Card>
						)}

						{/* Top Devotionals & Reader Insights */}
						<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
							<Card>
								<CardHeader>
									<CardTitle>Top Performing Devotionals</CardTitle>
									<CardDescription>Most viewed content this period</CardDescription>
								</CardHeader>
								<CardContent>
									{loading ? (
										<div className="space-y-4">
											{Array.from({ length: 5 }).map((_, i) => (
												<Skeleton key={i} className="h-16 w-full" />
											))}
										</div>
									) : topDevotionals.length > 0 ? (
										<div className="space-y-4">
											{topDevotionals.map((devotional, index) => (
												<div key={devotional.id} className="flex items-center gap-4">
													<div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-bold text-sm">
														{index + 1}
													</div>
													<div className="flex-1 min-w-0">
														<p className="font-medium text-sm truncate">{devotional.title}</p>
														<p className="text-xs text-muted-foreground">{devotional.author_name}</p>
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
									) : (
										<p className="text-center text-muted-foreground py-8">No devotionals found</p>
									)}
								</CardContent>
							</Card>

							<Card>
								<CardHeader>
									<CardTitle>Reader Insights</CardTitle>
									<CardDescription>Device breakdown, time patterns, and more</CardDescription>
								</CardHeader>
								<CardContent className="space-y-6">
									{loading ? (
										<div className="space-y-4">
											{Array.from({ length: 3 }).map((_, i) => (
												<Skeleton key={i} className="h-20 w-full" />
											))}
										</div>
									) : insights ? (
										<>
											<div>
												<h4 className="text-sm font-medium mb-3">Returning Readers</h4>
												<div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
													<span className="text-sm">{insights.returning_readers} / {insights.total_readers}</span>
													<span className="text-sm font-bold">{insights.returning_rate.toFixed(1)}%</span>
												</div>
											</div>

											<div>
												<h4 className="text-sm font-medium mb-3">Device Breakdown</h4>
												<div className="space-y-2">
													{Object.entries(insights.device_breakdown || {}).map(([device, count]: [string, any]) => {
														const Icon = getDeviceIcon(device);
														const total = Object.values(insights.device_breakdown || {}).reduce((a: number, b: any) => a + b, 0);
														const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
														return (
															<div key={device} className="flex items-center gap-3 p-2 rounded-lg bg-muted/50">
																<Icon className="w-4 h-4 text-muted-foreground" />
																<div className="flex-1">
																	<div className="flex items-center justify-between text-sm">
																		<span className="capitalize">{device}</span>
																		<span className="font-medium">{count} ({percentage}%)</span>
																	</div>
																	<div className="w-full bg-muted rounded-full h-2 mt-1">
																		<div
																			className="bg-primary h-2 rounded-full"
																			style={{ width: `${percentage}%` }}
																		/>
																	</div>
																</div>
															</div>
														);
													})}
												</div>
											</div>

											<div>
												<h4 className="text-sm font-medium mb-3">Peak Reading Times</h4>
												<div className="grid grid-cols-4 gap-2">
													{Object.entries(insights.time_of_day || {})
														.sort(([a], [b]) => a.localeCompare(b))
														.slice(0, 8)
														.map(([hour, count]: [string, any]) => {
															const maxCount = Math.max(...Object.values(insights.time_of_day || {}));
															return (
																<div key={hour} className="text-center p-2 rounded-lg bg-muted/50">
																	<p className="text-xs font-medium">{hour}</p>
																	<p className="text-xs text-muted-foreground">{count}</p>
																	<div className="w-full bg-muted rounded-full h-1 mt-1">
																		<div
																			className="bg-primary h-1 rounded-full"
																			style={{ width: `${(count / maxCount) * 100}%` }}
																		/>
																	</div>
																</div>
															);
														})}
												</div>
											</div>

											{Object.keys(insights.referral_sources || {}).length > 0 && (
												<div>
													<h4 className="text-sm font-medium mb-3">Referral Sources</h4>
													<div className="space-y-2">
														{Object.entries(insights.referral_sources || {}).map(([platform, count]: [string, any]) => (
															<div key={platform} className="flex items-center justify-between p-2 rounded-lg bg-muted/50">
																<div className="flex items-center gap-2">
																	<LinkIcon className="w-4 h-4 text-muted-foreground" />
																	<span className="text-sm capitalize">{platform}</span>
																</div>
																<span className="text-sm font-medium">{count}</span>
															</div>
														))}
													</div>
												</div>
											)}
										</>
									) : null}
								</CardContent>
							</Card>
						</div>

						{/* Audience Growth */}
						{growth && (
							<Card>
								<CardHeader>
									<CardTitle>Audience Growth & Retention</CardTitle>
									<CardDescription>New readers, retention, and churn metrics</CardDescription>
								</CardHeader>
								<CardContent>
									<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
										<div className="text-center p-4 rounded-lg bg-muted/50">
											<p className="text-2xl font-bold text-foreground">{growth.new_readers}</p>
											<p className="text-sm text-muted-foreground mt-1">New Readers</p>
										</div>
										<div className="text-center p-4 rounded-lg bg-green-500/10">
											<p className="text-2xl font-bold text-green-600">{growth.retention_rate.toFixed(1)}%</p>
											<p className="text-sm text-muted-foreground mt-1">Retention Rate</p>
											<p className="text-xs text-muted-foreground mt-1">{growth.retained_readers} retained</p>
										</div>
										<div className="text-center p-4 rounded-lg bg-red-500/10">
											<p className="text-2xl font-bold text-red-600">{growth.churn_rate.toFixed(1)}%</p>
											<p className="text-sm text-muted-foreground mt-1">Churn Rate</p>
											<p className="text-xs text-muted-foreground mt-1">{growth.churned_readers} churned</p>
										</div>
									</div>
								</CardContent>
							</Card>
						)}
					</div>
				</main>
			</div>
		</SidebarProvider>
	);
}

