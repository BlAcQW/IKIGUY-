import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { affiliateApi } from '@/lib/core-api';
import {
	TrendingUp,
	TrendingDown,
	MousePointerClick,
	UserPlus,
	Target,
	BarChart3,
	PieChart,
	Calendar
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ConversionAnalytics {
	total_clicks: number;
	total_conversions: number;
	conversion_rate: number;
	traffic_sources: Array<{
		source: string;
		clicks: number;
		conversions: number;
		conversion_rate: number;
	}>;
}

interface LinkPerformance {
	referral_code: string;
	utm_source?: string;
	utm_campaign?: string;
	utm_medium?: string;
	clicks: number;
	conversions: number;
	conversion_rate: number;
}

const AnalyticsDashboard: React.FC = () => {
	const [analytics, setAnalytics] = useState<ConversionAnalytics | null>(null);
	const [linkPerformance, setLinkPerformance] = useState<LinkPerformance[]>([]);
	const [timeRange, setTimeRange] = useState('30');
	const [isLoading, setIsLoading] = useState(false);
	const { toast } = useToast();

	useEffect(() => {
		loadAnalytics();
	}, [timeRange]);

	const loadAnalytics = async () => {
		setIsLoading(true);
		try {
			const days = parseInt(timeRange);
			const [analyticsData, linkData] = await Promise.all([
				affiliateApi.getConversionAnalytics(days),
				affiliateApi.getLinkPerformance(days)
			]);

			setAnalytics(analyticsData);
			setLinkPerformance(linkData.links || []);
		} catch (error: any) {
			console.error('Failed to load analytics:', error);
			toast({
				title: 'Error loading analytics',
				description: error.message || 'Failed to load analytics data',
				variant: 'destructive'
			});
		} finally {
			setIsLoading(false);
		}
	};

	const formatPercentage = (value: number) => {
		return `${value.toFixed(1)}%`;
	};

	const getConversionRateColor = (rate: number) => {
		if (rate >= 10) return 'text-green-600';
		if (rate >= 5) return 'text-blue-600';
		if (rate >= 2) return 'text-yellow-600';
		return 'text-gray-600';
	};

	const getConversionRateBadgeVariant = (rate: number): "default" | "secondary" | "destructive" | "outline" => {
		if (rate >= 10) return 'default';
		if (rate >= 5) return 'secondary';
		return 'outline';
	};

	if (isLoading && !analytics) {
		return (
			<div className="space-y-6">
				<div className="h-12 bg-gray-200 rounded animate-pulse w-64" />
				<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
					{[...Array(3)].map((_, i) => (
						<div key={i} className="h-32 bg-gray-200 rounded animate-pulse" />
					))}
				</div>
				<div className="h-96 bg-gray-200 rounded animate-pulse" />
			</div>
		);
	}

	return (
		<div className="space-y-6">
			{/* Header with Time Range Selector */}
			<div className="flex items-center justify-between">
				<div>
					<h2 className="text-2xl font-bold">Analytics Dashboard</h2>
					<p className="text-muted-foreground">Track your referral performance and conversion metrics</p>
				</div>
				<div className="flex items-center gap-2">
					<Calendar className="h-4 w-4 text-muted-foreground" />
					<Select value={timeRange} onValueChange={setTimeRange}>
						<SelectTrigger className="w-[180px]">
							<SelectValue placeholder="Select time range" />
						</SelectTrigger>
						<SelectContent>
							<SelectItem value="7">Last 7 days</SelectItem>
							<SelectItem value="30">Last 30 days</SelectItem>
							<SelectItem value="90">Last 90 days</SelectItem>
							<SelectItem value="365">Last year</SelectItem>
						</SelectContent>
					</Select>
					<Button
						variant="outline"
						size="sm"
						onClick={loadAnalytics}
						disabled={isLoading}
					>
						Refresh
					</Button>
				</div>
			</div>

			{/* Key Metrics Cards */}
			{analytics && (
				<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
					<Card>
						<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
							<CardTitle className="text-sm font-medium">Total Clicks</CardTitle>
							<MousePointerClick className="h-4 w-4 text-muted-foreground" />
						</CardHeader>
						<CardContent>
							<div className="text-2xl font-bold">{analytics.total_clicks.toLocaleString()}</div>
							<p className="text-xs text-muted-foreground">
								Referral link clicks in last {timeRange} days
							</p>
						</CardContent>
					</Card>

					<Card>
						<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
							<CardTitle className="text-sm font-medium">Total Conversions</CardTitle>
							<UserPlus className="h-4 w-4 text-muted-foreground" />
						</CardHeader>
						<CardContent>
							<div className="text-2xl font-bold">{analytics.total_conversions.toLocaleString()}</div>
							<p className="text-xs text-muted-foreground">
								Successful signups from clicks
							</p>
						</CardContent>
					</Card>

					<Card>
						<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
							<CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
							<Target className="h-4 w-4 text-muted-foreground" />
						</CardHeader>
						<CardContent>
							<div className={`text-2xl font-bold ${getConversionRateColor(analytics.conversion_rate)}`}>
								{formatPercentage(analytics.conversion_rate)}
							</div>
							<p className="text-xs text-muted-foreground">
								{analytics.conversion_rate >= 5 ? '🎯 Great performance!' : 'Keep promoting!'}
							</p>
						</CardContent>
					</Card>
				</div>
			)}

			{/* Traffic Sources Breakdown */}
			{analytics && analytics.traffic_sources && analytics.traffic_sources.length > 0 && (
				<Card>
					<CardHeader>
						<CardTitle className="flex items-center gap-2">
							<PieChart className="h-5 w-5" />
							Traffic Sources
						</CardTitle>
						<CardDescription>
							Performance breakdown by traffic source
						</CardDescription>
					</CardHeader>
					<CardContent>
						<div className="space-y-4">
							{analytics.traffic_sources.map((source, index) => {
								const percentage = analytics.total_clicks > 0
									? (source.clicks / analytics.total_clicks) * 100
									: 0;

								return (
									<div key={index} className="space-y-2">
										<div className="flex items-center justify-between">
											<div className="flex items-center gap-3">
												<div className="font-medium">
													{source.source || 'Direct'}
												</div>
												<Badge variant={getConversionRateBadgeVariant(source.conversion_rate)}>
													{formatPercentage(source.conversion_rate)} conversion
												</Badge>
											</div>
											<div className="text-sm text-muted-foreground">
												{source.clicks} clicks • {source.conversions} conversions
											</div>
										</div>
										<div className="w-full bg-gray-200 rounded-full h-2">
											<div
												className="bg-blue-600 h-2 rounded-full transition-all"
												style={{ width: `${percentage}%` }}
											/>
										</div>
									</div>
								);
							})}
						</div>
					</CardContent>
				</Card>
			)}

			{/* Link Performance Table */}
			{linkPerformance.length > 0 && (
				<Card>
					<CardHeader>
						<CardTitle className="flex items-center gap-2">
							<BarChart3 className="h-5 w-5" />
							Link Performance
						</CardTitle>
						<CardDescription>
							Individual link performance metrics
						</CardDescription>
					</CardHeader>
					<CardContent>
						<div className="overflow-x-auto">
							<table className="w-full">
								<thead>
									<tr className="border-b">
										<th className="text-left py-3 px-4 font-medium">Link</th>
										<th className="text-left py-3 px-4 font-medium">Source</th>
										<th className="text-left py-3 px-4 font-medium">Campaign</th>
										<th className="text-right py-3 px-4 font-medium">Clicks</th>
										<th className="text-right py-3 px-4 font-medium">Conversions</th>
										<th className="text-right py-3 px-4 font-medium">Rate</th>
									</tr>
								</thead>
								<tbody>
									{linkPerformance.map((link, index) => (
										<tr key={index} className="border-b hover:bg-gray-50">
											<td className="py-3 px-4">
												<code className="text-xs bg-gray-100 px-2 py-1 rounded">
													{link.referral_code}
												</code>
											</td>
											<td className="py-3 px-4 text-sm">
												{link.utm_source || '-'}
											</td>
											<td className="py-3 px-4 text-sm">
												{link.utm_campaign || '-'}
											</td>
											<td className="py-3 px-4 text-right font-medium">
												{link.clicks}
											</td>
											<td className="py-3 px-4 text-right font-medium">
												{link.conversions}
											</td>
											<td className="py-3 px-4 text-right">
												<span className={`font-semibold ${getConversionRateColor(link.conversion_rate)}`}>
													{formatPercentage(link.conversion_rate)}
												</span>
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					</CardContent>
				</Card>
			)}

			{/* Empty State */}
			{analytics && analytics.total_clicks === 0 && (
				<Card>
					<CardContent className="py-12">
						<div className="text-center space-y-3">
							<BarChart3 className="h-12 w-12 text-gray-400 mx-auto" />
							<h3 className="text-lg font-medium">No analytics data yet</h3>
							<p className="text-sm text-muted-foreground max-w-md mx-auto">
								Start sharing your referral links to see analytics data here.
								Track clicks, conversions, and optimize your campaigns.
							</p>
						</div>
					</CardContent>
				</Card>
			)}
		</div>
	);
};

export default AnalyticsDashboard;
