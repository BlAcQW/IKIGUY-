import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { 
	Calendar as CalendarIcon, 
	AlertCircle, 
	Clock, 
	ChevronLeft, 
	ChevronRight, 
	Bell,
	Grid3x3,
	List,
	GripVertical
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import {
	SidebarProvider,
	SidebarTrigger,
} from "@/components/ui/sidebar";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import { CalendarDayDialog } from "@/components/admin/CalendarDayDialog";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, addMonths, subMonths, startOfWeek, endOfWeek } from "date-fns";
import { useDrag, useDrop, DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";

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
	status: 'draft' | 'scheduled' | 'published';
	scheduled_date: string;
	series_id?: string;
	series_name?: string;
	part_number?: number;
}

interface ScheduleGap {
	date: string;
	day_of_week: string;
}

interface SeriesItem {
	series_id: string;
	series_name: string;
	devotionals_count: number;
	start_date: string | null;
	end_date: string | null;
}

// Draggable Series Bar Component
const DraggableSeriesBar = ({
	series,
	isStart,
	isEnd,
	onMoveSeries
}: {
	series: SeriesItem;
	isStart: boolean;
	isEnd: boolean;
	onMoveSeries?: (seriesId: string, newDate: Date) => Promise<void>;
}) => {
	const [{ isDragging }, drag] = useDrag({
		type: 'series',
		item: { id: series.series_id, series },
		collect: (monitor) => ({
			isDragging: monitor.isDragging(),
		}),
		canDrag: isStart && !!onMoveSeries, // Only allow dragging from the start date if handler exists
	});

	return (
		<div
			ref={isStart ? drag : undefined}
			className={`h-2 bg-purple-500/30 border border-purple-500/50 rounded flex items-center transition-opacity ${
				isStart && onMoveSeries ? 'cursor-move' : 'cursor-default'
			} ${
				isStart ? 'rounded-l-md' : ''
			} ${isEnd ? 'rounded-r-md' : ''} ${
				!isStart && !isEnd ? 'rounded-none' : ''
			} ${isDragging ? 'opacity-50' : 'opacity-100'} ${
				isStart && onMoveSeries ? 'hover:bg-purple-500/40' : ''
			}`}
			title={isStart 
				? onMoveSeries
					? `${series.series_name} (${series.devotionals_count} parts) - Drag to move series`
					: `${series.series_name} (${series.devotionals_count} parts)`
				: `${series.series_name} (${series.devotionals_count} parts)`
			}
		>
			{isStart && (
				<span className="text-[8px] px-1 text-purple-700 font-medium truncate flex items-center gap-1">
					{onMoveSeries && <GripVertical className="w-2 h-2" />}
					{series.series_name}
				</span>
			)}
		</div>
	);
};

// Draggable Devotional Card Component
const DraggableDevotionalCard = ({ 
	devotional, 
	onDrop 
}: { 
	devotional: DevotionalItem;
	onDrop: (devotionalId: string, newDate: Date) => Promise<void>;
}) => {
	const [{ isDragging }, drag] = useDrag({
		type: 'devotional',
		item: { id: devotional.devotional_id, devotional },
		collect: (monitor) => ({
			isDragging: monitor.isDragging(),
		}),
	});

	const getStatusColor = (status: string) => {
		switch (status) {
			case 'published':
				return 'bg-green-500/20 text-green-700 border-green-500/30';
			case 'scheduled':
				return 'bg-blue-500/20 text-blue-700 border-blue-500/30';
			case 'draft':
				return 'bg-gray-500/20 text-gray-700 border-gray-500/30';
			default:
				return 'bg-muted text-muted-foreground border-border';
		}
	};

	return (
		<div
			ref={drag}
			className={`p-2 rounded-lg border text-xs cursor-move transition-opacity ${
				getStatusColor(devotional.status)
			} ${isDragging ? 'opacity-50' : 'opacity-100'}`}
		>
			<div className="flex items-start gap-1">
				<GripVertical className="w-3 h-3 mt-0.5 flex-shrink-0" />
				<div className="flex-1 min-w-0">
					<p className="font-medium truncate">{devotional.title}</p>
					{devotional.series_name && (
						<p className="text-[10px] opacity-75 truncate">
							{devotional.series_name} {devotional.part_number ? `Part ${devotional.part_number}` : ''}
						</p>
					)}
					<Badge variant="outline" className="mt-1 text-[10px] px-1 py-0">
						{devotional.status}
					</Badge>
				</div>
			</div>
		</div>
	);
};

// Droppable Calendar Day Component
const DroppableDay = ({ 
	date, 
	devotionals,
	series,
	getSeriesForDate,
	isSeriesStart,
	isSeriesEnd,
	onDrop,
	onMoveSeries,
	onClick,
	isCurrentMonth,
	isTodayDate
}: { 
	date: Date;
	devotionals: DevotionalItem[];
	series: SeriesItem[];
	getSeriesForDate: (date: Date) => SeriesItem[];
	isSeriesStart: (date: Date, series: SeriesItem) => boolean;
	isSeriesEnd: (date: Date, series: SeriesItem) => boolean;
	onDrop: (devotionalId: string, newDate: Date) => Promise<void>;
	onMoveSeries?: (seriesId: string, newDate: Date) => Promise<void>;
	onClick: (date: Date) => void;
	isCurrentMonth: boolean;
	isTodayDate: boolean;
}) => {
	const [{ isOver }, drop] = useDrop({
		accept: ['devotional', 'series'],
		drop: (item: { id: string; devotional?: DevotionalItem; series?: SeriesItem }, monitor) => {
			if (monitor.getItemType() === 'series' && item.series) {
				// Handle series drop
				onMoveSeries?.(item.series.series_id, date);
			} else if (monitor.getItemType() === 'devotional' && item.devotional) {
				// Handle devotional drop
				onDrop(item.id, date);
			}
		},
		collect: (monitor) => ({
			isOver: monitor.isOver(),
		}),
	});

	const getStatusCounts = () => {
		const counts = { published: 0, scheduled: 0, draft: 0 };
		devotionals.forEach(d => {
			if (counts.hasOwnProperty(d.status)) {
				counts[d.status as keyof typeof counts]++;
			}
		});
		return counts;
	};

	const counts = getStatusCounts();
	const hasContent = devotionals.length > 0;
	const daySeries = getSeriesForDate(date);
	const standaloneDevotionals = devotionals.filter(d => !d.series_id);

	return (
		<div
			ref={drop}
			onClick={() => onClick(date)}
			className={`min-h-[100px] p-1 border rounded-lg transition-colors cursor-pointer hover:bg-accent/50 relative ${
				isCurrentMonth 
					? 'bg-background border-border' 
					: 'bg-muted/30 border-border/50'
			} ${
				isTodayDate 
					? 'ring-2 ring-primary' 
					: ''
			} ${
				isOver 
					? 'bg-primary/20 border-primary border-2' 
					: ''
			}`}
		>
			<div className={`text-xs font-medium mb-1 ${
				isCurrentMonth ? 'text-foreground' : 'text-muted-foreground'
			} ${isTodayDate ? 'text-primary font-bold' : ''}`}>
				{format(date, 'd')}
			</div>
			
			{/* Series bars - displayed as horizontal bars spanning multiple days */}
			{daySeries.length > 0 && (
				<div className="space-y-0.5 mb-1">
					{daySeries.map((seriesItem) => {
						const isStart = isSeriesStart(date, seriesItem);
						const isEnd = isSeriesEnd(date, seriesItem);
						return (
							<DraggableSeriesBar
								key={seriesItem.series_id}
								series={seriesItem}
								isStart={isStart}
								isEnd={isEnd}
								onMove={onMoveSeries}
							/>
						);
					})}
				</div>
			)}
			
			{hasContent && (
				<div className="space-y-1">
					{/* Status indicators for standalone devotionals only */}
					{standaloneDevotionals.length > 0 && (
						<>
							{counts.published > 0 && (
								<div className="h-1.5 bg-green-500 rounded-full" title={`${counts.published} published`} />
							)}
							{counts.scheduled > 0 && (
								<div className="h-1.5 bg-blue-500 rounded-full" title={`${counts.scheduled} scheduled`} />
							)}
							{counts.draft > 0 && (
								<div className="h-1.5 bg-gray-500 rounded-full" title={`${counts.draft} draft`} />
							)}
						</>
					)}
					{standaloneDevotionals.length > 3 && (
						<p className="text-[10px] text-muted-foreground mt-1">
							+{standaloneDevotionals.length - 3} more
						</p>
					)}
					{standaloneDevotionals.slice(0, 3).map((dev) => (
						<div
							key={dev.devotional_id}
							onClick={(e) => e.stopPropagation()}
						>
							<DraggableDevotionalCard 
								devotional={dev}
								onDrop={onDrop}
							/>
						</div>
					))}
				</div>
			)}
		</div>
	);
};

const CalendarGridView = () => {
	const { toast } = useToast();
	const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
	const [stats, setStats] = useState<CalendarStats | null>(null);
	const [devotionals, setDevotionals] = useState<DevotionalItem[]>([]);
	const [series, setSeries] = useState<SeriesItem[]>([]);
	const [gaps, setGaps] = useState<ScheduleGap[]>([]);
	const [loading, setLoading] = useState(true);
	const [currentMonth, setCurrentMonth] = useState(new Date());
	const [statusFilter, setStatusFilter] = useState<string>("all");
	const [isRescheduling, setIsRescheduling] = useState<string | null>(null);
	const [selectedDate, setSelectedDate] = useState<Date | null>(null);
	const [isDayDialogOpen, setIsDayDialogOpen] = useState(false);

	useEffect(() => {
		fetchCalendarData();
	}, [currentMonth, statusFilter]);

	const fetchCalendarData = async () => {
		try {
			setLoading(true);

			const startDate = startOfMonth(currentMonth);
			const endDate = endOfMonth(currentMonth);

			const [statsData, devotionalsData, gapsData] = await Promise.all([
				apiClient.getCalendarStats(),
				apiClient.getCalendarDevotionals({
					start_date: format(startDate, 'yyyy-MM-dd'),
					end_date: format(endDate, 'yyyy-MM-dd'),
					status: statusFilter === "all" ? undefined : statusFilter as any,
				}),
				apiClient.getScheduleGaps({
					start_date: format(startDate, 'yyyy-MM-dd'),
					end_date: format(endDate, 'yyyy-MM-dd'),
				}),
			]);

			setStats(statsData);
			setDevotionals(devotionalsData.devotionals || []);
			setSeries(devotionalsData.series || []);
			setGaps(gapsData.gaps || []);
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

	const handleReschedule = async (devotionalId: string, newDate: Date) => {
		if (isRescheduling) return; // Prevent concurrent reschedules

		setIsRescheduling(devotionalId);
		try {
			// Set time to 8 AM for scheduled devotionals
			const scheduledDateTime = new Date(newDate);
			scheduledDateTime.setHours(8, 0, 0, 0);

			await apiClient.updateDevotional(devotionalId, {
				scheduled_at: scheduledDateTime.toISOString(),
			});

			// Optimistic update
			setDevotionals(prev => 
				prev.map(d => 
					d.devotional_id === devotionalId 
						? { ...d, scheduled_date: scheduledDateTime.toISOString() }
						: d
				)
			);

			toast({
				title: "Rescheduled",
				description: "Devotional has been rescheduled successfully",
			});
		} catch (error: any) {
			console.error("Failed to reschedule:", error);
			toast({
				title: "Error",
				description: error.response?.data?.detail || "Failed to reschedule devotional",
				variant: "destructive",
			});
			// Reload on error
			fetchCalendarData();
		} finally {
			setIsRescheduling(null);
		}
	};

	const handleMoveSeries = async (seriesId: string, newStartDate: Date) => {
		if (isRescheduling) return; // Prevent concurrent operations

		setIsRescheduling(seriesId);
		try {
			const dateStr = format(newStartDate, 'yyyy-MM-dd');
			const result = await apiClient.moveSeries(seriesId, dateStr);

			toast({
				title: "Series Moved",
				description: result.message || `Series moved. ${result.rescheduled_count} devotionals rescheduled.`,
			});

			// Reload calendar data to reflect changes
			fetchCalendarData();
		} catch (error: any) {
			console.error("Failed to move series:", error);
			toast({
				title: "Error",
				description: error.response?.data?.detail || "Failed to move series",
				variant: "destructive",
			});
		} finally {
			setIsRescheduling(null);
		}
	};

	const getDevotionalsForDate = (date: Date): DevotionalItem[] => {
		const dateStr = format(date, 'yyyy-MM-dd');
		return devotionals.filter(d => {
			if (!d.scheduled_date) return false;
			const devotionalDate = format(new Date(d.scheduled_date), 'yyyy-MM-dd');
			return devotionalDate === dateStr;
		});
	};

	const getSeriesForDate = (date: Date): SeriesItem[] => {
		const dateStr = format(date, 'yyyy-MM-dd');
		return series.filter(s => {
			if (!s.start_date || !s.end_date) return false;
			const start = format(new Date(s.start_date), 'yyyy-MM-dd');
			const end = format(new Date(s.end_date), 'yyyy-MM-dd');
			return dateStr >= start && dateStr <= end;
		});
	};

	const isSeriesStart = (date: Date, seriesItem: SeriesItem): boolean => {
		if (!seriesItem.start_date) return false;
		return format(date, 'yyyy-MM-dd') === format(new Date(seriesItem.start_date), 'yyyy-MM-dd');
	};

	const isSeriesEnd = (date: Date, seriesItem: SeriesItem): boolean => {
		if (!seriesItem.end_date) return false;
		return format(date, 'yyyy-MM-dd') === format(new Date(seriesItem.end_date), 'yyyy-MM-dd');
	};

	const hasGap = (date: Date) => {
		const dateStr = format(date, 'yyyy-MM-dd');
		return gaps.some(g => g.date === dateStr);
	};

	const nextMonth = () => {
		setCurrentMonth(addMonths(currentMonth, 1));
	};

	const prevMonth = () => {
		setCurrentMonth(subMonths(currentMonth, 1));
	};

	const handleDayClick = (date: Date) => {
		setSelectedDate(date);
		setIsDayDialogOpen(true);
	};

	const handleDialogClose = () => {
		setIsDayDialogOpen(false);
		setSelectedDate(null);
	};

	const handleRefresh = () => {
		fetchCalendarData();
	};

	// Generate calendar grid
	const monthStart = startOfMonth(currentMonth);
	const monthEnd = endOfMonth(currentMonth);
	const calendarStart = startOfWeek(monthStart);
	const calendarEnd = endOfWeek(monthEnd);
	const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

	// Group devotionals by date for list view
	const devotionalsByDate = devotionals.reduce((acc, dev) => {
		if (!dev.scheduled_date) return acc;
		const dateKey = format(new Date(dev.scheduled_date), 'yyyy-MM-dd');
		if (!acc[dateKey]) acc[dateKey] = [];
		acc[dateKey].push(dev);
		return acc;
	}, {} as Record<string, DevotionalItem[]>);

	return (
		<DndProvider backend={HTML5Backend}>
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
								<div className="flex items-center gap-2">
									<Button
										variant={viewMode === 'grid' ? 'default' : 'outline'}
										size="sm"
										onClick={() => setViewMode('grid')}
									>
										<Grid3x3 className="w-4 h-4 mr-2" />
										Grid
									</Button>
									<Button
										variant={viewMode === 'list' ? 'default' : 'outline'}
										size="sm"
										onClick={() => setViewMode('list')}
									>
										<List className="w-4 h-4 mr-2" />
										List
									</Button>
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

							{/* Calendar Grid View */}
							{viewMode === 'grid' ? (
								<Card>
									<CardHeader>
										<div className="flex items-center justify-between">
											<CardTitle>
												{format(currentMonth, 'MMMM yyyy')}
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
										{/* Weekday Headers */}
										<div className="grid grid-cols-7 gap-2 mb-2">
											{['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
												<div key={day} className="text-center text-sm font-medium text-muted-foreground py-2">
													{day}
												</div>
											))}
										</div>

										{/* Calendar Grid */}
										<div className="grid grid-cols-7 gap-2">
											{days.map((date) => {
												const dayDevotionals = getDevotionalsForDate(date);
												const isCurrentMonthDay = isSameMonth(date, currentMonth);
												const isTodayDate = isToday(date);
												const hasGapDay = hasGap(date);

												return (
													<DroppableDay
														key={date.toISOString()}
														date={date}
														devotionals={dayDevotionals}
														series={series}
														getSeriesForDate={getSeriesForDate}
														isSeriesStart={isSeriesStart}
														isSeriesEnd={isSeriesEnd}
														onDrop={handleReschedule}
														onMoveSeries={handleMoveSeries}
														onClick={handleDayClick}
														isCurrentMonth={isCurrentMonthDay}
														isTodayDate={isTodayDate}
													/>
												);
											})}
										</div>

										{/* Legend */}
										<div className="flex items-center gap-4 mt-6 text-sm flex-wrap">
											<div className="flex items-center gap-2">
												<div className="w-4 h-4 rounded bg-green-500" />
												<span className="text-muted-foreground">Published</span>
											</div>
											<div className="flex items-center gap-2">
												<div className="w-4 h-4 rounded bg-blue-500" />
												<span className="text-muted-foreground">Scheduled</span>
											</div>
											<div className="flex items-center gap-2">
												<div className="w-4 h-4 rounded bg-gray-500" />
												<span className="text-muted-foreground">Draft</span>
											</div>
											<div className="flex items-center gap-2">
												<div className="w-4 h-2 rounded bg-purple-500/30 border border-purple-500/50" />
												<span className="text-muted-foreground">Series</span>
											</div>
											<div className="flex items-center gap-2">
												<GripVertical className="w-4 h-4 text-muted-foreground" />
												<span className="text-muted-foreground">Drag to reschedule</span>
											</div>
										</div>
									</CardContent>
								</Card>
							) : (
								/* List View */
								<Card>
									<CardHeader>
										<div className="flex items-center justify-between">
											<CardTitle>
												{format(currentMonth, 'MMMM yyyy')} - List View
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
										<div className="space-y-4">
											{Object.entries(devotionalsByDate)
												.sort(([a], [b]) => a.localeCompare(b))
												.map(([dateStr, dayDevotionals]) => {
													const date = new Date(dateStr);
													return (
														<div key={dateStr} className="border rounded-lg p-4">
															<h3 className="font-semibold mb-3">
																{format(date, 'EEEE, MMMM d, yyyy')}
															</h3>
															<div className="space-y-2">
																{dayDevotionals.map(dev => (
																	<DraggableDevotionalCard
																		key={dev.devotional_id}
																		devotional={dev}
																		onDrop={handleReschedule}
																	/>
																))}
															</div>
														</div>
													);
												})}
											{Object.keys(devotionalsByDate).length === 0 && (
												<p className="text-center text-muted-foreground py-8">
													No devotionals scheduled for this month
												</p>
											)}
										</div>
									</CardContent>
								</Card>
							)}
						</div>
					</div>
				</div>
			</SidebarProvider>

			{/* Calendar Day Dialog */}
			{selectedDate && (
				<CalendarDayDialog
					open={isDayDialogOpen}
					onOpenChange={handleDialogClose}
					date={selectedDate}
					devotionals={getDevotionalsForDate(selectedDate)}
					onRefresh={handleRefresh}
				/>
			)}
		</DndProvider>
	);
};

export default CalendarGridView;

