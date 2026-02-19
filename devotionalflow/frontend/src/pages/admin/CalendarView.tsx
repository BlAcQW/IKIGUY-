import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Calendar as CalendarIcon, AlertCircle, TrendingUp, Clock, ChevronLeft, ChevronRight, Bell } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
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

interface CalendarStats {
	total_published: number;
	this_month: number;
	this_week: number;
	today: number;
	upcoming_scheduled: number;
	publishing_streak: number;
}

interface DevotionalItem {
	devotional_id: string;
	title: string;
	author_name: string;
	status: string;
	scheduled_date: string;
}

interface ScheduleGap {
	date: string;
	day_of_week: string;
}

const CalendarView = () => {
	const { toast } = useToast();
	const [stats, setStats] = useState<CalendarStats | null>(null);
	const [devotionals, setDevotionals] = useState<DevotionalItem[]>([]);
	const [gaps, setGaps] = useState<ScheduleGap[]>([]);
	const [upcoming, setUpcoming] = useState<DevotionalItem[]>([]);
	const [loading, setLoading] = useState(true);
	const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
	const [currentMonth, setCurrentMonth] = useState(new Date());
	const [statusFilter, setStatusFilter] = useState<string>("all");

	useEffect(() => {
		fetchCalendarData();
	}, [currentMonth, statusFilter]);

	const fetchCalendarData = async () => {
		try {
			setLoading(true);

			const startDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
			const endDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0);

			const [statsData, devotionalsData, gapsData, upcomingData] = await Promise.all([
				apiClient.getCalendarStats(),
				apiClient.getCalendarDevotionals({
					start_date: startDate.toISOString().split('T')[0],
					end_date: endDate.toISOString().split('T')[0],
					status: statusFilter === "all" ? undefined : statusFilter as any,
				}),
				apiClient.getScheduleGaps({
					start_date: startDate.toISOString().split('T')[0],
					end_date: endDate.toISOString().split('T')[0],
				}),
				apiClient.getUpcomingDevotionals({ days: 7, limit: 5 }),
			]);

			setStats(statsData);
			setDevotionals(devotionalsData.devotionals || []);
			setGaps(gapsData.gaps || []);
			setUpcoming(upcomingData.devotionals || []);
		} catch (error: any) {
			console.error("Failed to fetch calendar data:", error);
			toast({
				title: "Error",
				description: error.response?.data?.detail || "Failed to load calendar data",
				variant: "destructive",
			});
		} finally {
			setLoading(false);
		}
	};

	const getDevotionalsForDate = (date: Date) => {
		const dateStr = date.toISOString().split('T')[0];
		return devotionals.filter(d => d.scheduled_date && typeof d.scheduled_date === 'string' && d.scheduled_date.split('T')[0] === dateStr);
	};

	const hasGap = (date: Date) => {
		const dateStr = date.toISOString().split('T')[0];
		return gaps.some(g => g.date === dateStr);
	};

	const nextMonth = () => {
		setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1));
	};

	const prevMonth = () => {
		setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1));
	};

	return (
		<SidebarProvider>
			<div className="min-h-screen flex w-full bg-background">
				<AdminSidebar />

				<div className="flex-1 overflow-auto">
					{/* Header */}
					<header className="sticky top-0 z-10 border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
						<div className="flex h-16 items-center gap-4 px-6">
							<SidebarTrigger className="md:hidden" />
							<div className="flex-1">
								<h1 className="text-xl font-serif font-bold text-foreground">Content Calendar</h1>
								<p className="text-sm text-muted-foreground">Schedule and manage devotional publications</p>
							</div>
							<Select value={statusFilter} onValueChange={setStatusFilter}>
								<SelectTrigger className="w-40">
									<SelectValue />
								</SelectTrigger>
								<SelectContent>
									<SelectItem value="all">All Status</SelectItem>
									<SelectItem value="published">Published</SelectItem>
									<SelectItem value="scheduled">Scheduled</SelectItem>
									<SelectItem value="draft">Draft</SelectItem>
								</SelectContent>
							</Select>
							<Button variant="outline" size="icon">
								<Bell className="w-4 h-4" />
							</Button>
						</div>
					</header>

					{/* Content */}
					<div className="p-6 space-y-6">
						{/* Stats */}
						<div className="grid sm:grid-cols-2 lg:grid-cols-6 gap-4">
							{loading ? (
								Array.from({ length: 6 }).map((_, i) => (
									<Card key={i}>
										<CardContent className="p-4">
											<Skeleton className="h-4 w-20 mb-2" />
											<Skeleton className="h-8 w-16" />
										</CardContent>
									</Card>
								))
							) : stats ? (
								[
									{ label: "Total Published", value: stats.total_published },
									{ label: "This Month", value: stats.this_month },
									{ label: "This Week", value: stats.this_week },
									{ label: "Today", value: stats.today },
									{ label: "Upcoming", value: stats.upcoming_scheduled },
									{ label: "Streak", value: `${stats.publishing_streak} days` },
								].map((stat, i) => (
									<Card key={i}>
										<CardContent className="p-4">
											<p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
											<p className="text-2xl font-bold text-foreground">{stat.value}</p>
										</CardContent>
									</Card>
								))
							) : null}
						</div>

						<div className="grid lg:grid-cols-3 gap-6">
							{/* Calendar */}
							<Card className="lg:col-span-2">
								<CardHeader>
									<div className="flex items-center justify-between">
										<CardTitle>
											{currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
										</CardTitle>
										<div className="flex gap-2">
											<Button variant="outline" size="icon" onClick={prevMonth}>
												<ChevronLeft className="w-4 h-4" />
											</Button>
											<Button variant="outline" size="icon" onClick={nextMonth}>
												<ChevronRight className="w-4 h-4" />
											</Button>
										</div>
									</div>
								</CardHeader>
								<CardContent>
									<Calendar
										mode="single"
										selected={selectedDate}
										onSelect={setSelectedDate}
										month={currentMonth}
										onMonthChange={setCurrentMonth}
										className="rounded-md border"
										modifiers={{
											hasContent: (date) => getDevotionalsForDate(date).length > 0,
											hasGap: (date) => hasGap(date),
										}}
										modifiersStyles={{
											hasContent: { backgroundColor: 'var(--accent)', color: 'white' },
											hasGap: { backgroundColor: 'var(--destructive)', color: 'white' },
										}}
									/>

									{/* Legend */}
									<div className="flex items-center gap-4 mt-4 text-sm">
										<div className="flex items-center gap-2">
											<div className="w-4 h-4 rounded bg-accent" />
											<span className="text-muted-foreground">Has Content</span>
										</div>
										<div className="flex items-center gap-2">
											<div className="w-4 h-4 rounded bg-destructive" />
											<span className="text-muted-foreground">Gap</span>
										</div>
									</div>

									{/* Selected Date Content */}
									{selectedDate && (
										<div className="mt-6">
											<h3 className="font-semibold mb-3">
												{selectedDate.toLocaleDateString('en-US', {
													weekday: 'long',
													year: 'numeric',
													month: 'long',
													day: 'numeric'
												})}
											</h3>
											{getDevotionalsForDate(selectedDate).length > 0 ? (
												<div className="space-y-2">
													{getDevotionalsForDate(selectedDate).map((dev) => (
														<div key={dev.devotional_id} className="p-3 bg-muted rounded-lg">
															<p className="font-medium text-foreground">{dev.title}</p>
															<p className="text-sm text-muted-foreground">By {dev.author_name}</p>
															<Badge variant={dev.status === 'published' ? 'default' : 'secondary'} className="mt-2">
																{dev.status}
															</Badge>
														</div>
													))}
												</div>
											) : (
												<p className="text-muted-foreground text-sm">No devotionals scheduled</p>
											)}
										</div>
									)}
								</CardContent>
							</Card>

							{/* Sidebar */}
							<div className="space-y-6">
								{/* Schedule Gaps */}
								<Card>
									<CardHeader>
										<CardTitle className="flex items-center gap-2">
											<AlertCircle className="w-5 h-5 text-destructive" />
											Schedule Gaps
										</CardTitle>
									</CardHeader>
									<CardContent>
										{loading ? (
											<div className="space-y-2">
												{Array.from({ length: 3 }).map((_, i) => (
													<Skeleton key={i} className="h-12 w-full" />
												))}
											</div>
										) : gaps.length > 0 ? (
											<div className="space-y-2">
												{gaps.slice(0, 5).map((gap, i) => (
													<div key={i} className="p-3 bg-destructive/10 rounded-lg border border-destructive/20">
														<p className="font-medium text-foreground">
															{new Date(gap.date).toLocaleDateString('en-US', {
																month: 'short',
																day: 'numeric'
															})}
														</p>
														<p className="text-sm text-muted-foreground">{gap.day_of_week}</p>
													</div>
												))}
												{gaps.length > 5 && (
													<p className="text-xs text-muted-foreground text-center mt-2">
														+{gaps.length - 5} more gaps
													</p>
												)}
											</div>
										) : (
											<p className="text-muted-foreground text-sm">No gaps in schedule!</p>
										)}
									</CardContent>
								</Card>

								{/* Upcoming */}
								<Card>
									<CardHeader>
										<CardTitle className="flex items-center gap-2">
											<Clock className="w-5 h-5 text-accent" />
											Coming Up
										</CardTitle>
									</CardHeader>
									<CardContent>
										{loading ? (
											<div className="space-y-2">
												{Array.from({ length: 3 }).map((_, i) => (
													<Skeleton key={i} className="h-16 w-full" />
												))}
											</div>
										) : upcoming.length > 0 ? (
											<div className="space-y-3">
												{upcoming.map((dev) => (
													<div key={dev.devotional_id} className="p-3 bg-muted/50 rounded-lg">
														<p className="font-medium text-foreground text-sm line-clamp-1">
															{dev.title}
														</p>
														<p className="text-xs text-muted-foreground mt-1">
															{new Date(dev.scheduled_date).toLocaleDateString('en-US', {
																month: 'short',
																day: 'numeric',
																hour: 'numeric',
																minute: '2-digit',
															})}
														</p>
													</div>
												))}
											</div>
										) : (
											<p className="text-muted-foreground text-sm">No upcoming devotionals</p>
										)}
									</CardContent>
								</Card>
							</div>
						</div>
					</div>
				</div>
			</div>
		</SidebarProvider>
	);
};

export default CalendarView;
