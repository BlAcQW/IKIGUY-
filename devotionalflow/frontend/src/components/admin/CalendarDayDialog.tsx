import { useState, useEffect } from "react";
import { format } from "date-fns";
import { Calendar, BookOpen, Plus, Edit, ExternalLink } from "lucide-react";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";

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

interface SeriesItem {
	id: string;
	name: string;
	description?: string;
	start_date?: string;
	devotionals_count: number;
}

interface CalendarDayDialogProps {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	date: Date | null;
	devotionals: DevotionalItem[];
	onRefresh?: () => void;
}

export function CalendarDayDialog({
	open,
	onOpenChange,
	date,
	devotionals: initialDevotionals,
	onRefresh,
}: CalendarDayDialogProps) {
	const { toast } = useToast();
	const navigate = useNavigate();
	const [loading, setLoading] = useState(false);
	const [series, setSeries] = useState<SeriesItem[]>([]);
	const [devotionals, setDevotionals] = useState<DevotionalItem[]>(initialDevotionals);

	useEffect(() => {
		setDevotionals(initialDevotionals);
	}, [initialDevotionals]);

	useEffect(() => {
		if (open && date) {
			fetchDayData();
		}
	}, [open, date]);

	const fetchDayData = async () => {
		if (!date) return;

		setLoading(true);
		try {
			const dateStr = format(date, 'yyyy-MM-dd');
			
			// Fetch series that have devotionals on this date or start on this date
			const allSeries = await apiClient.listSeries();
			
			// Filter series that:
			// 1. Start on this date, OR
			// 2. Have devotionals scheduled on this date
			const relevantSeries: SeriesItem[] = [];

			for (const s of allSeries) {
				const seriesStartDate = s.start_date ? format(new Date(s.start_date), 'yyyy-MM-dd') : null;
				const hasDevotionalOnDate = devotionals.some(d => d.series_id === s.id);
				
				if (seriesStartDate === dateStr || hasDevotionalOnDate) {
					relevantSeries.push({
						id: s.id,
						name: s.name,
						description: s.description,
						start_date: s.start_date,
						devotionals_count: s.devotionals_count || 0,
					});
				}
			}

			setSeries(relevantSeries);
		} catch (error: any) {
			console.error("Failed to fetch day data:", error);
			toast({
				title: "Error",
				description: error.response?.data?.detail || "Failed to load day data",
				variant: "destructive",
			});
		} finally {
			setLoading(false);
		}
	};

	const handleCreateSeries = () => {
		if (!date) return;
		const dateStr = format(date, 'yyyy-MM-dd');
		// Navigate to series management or open series creation dialog
		// For now, navigate to compose with series creation
		navigate(`/admin/compose?date=${dateStr}&createSeries=true`);
		onOpenChange(false);
	};

	const handleCreateDevotional = (seriesId?: string) => {
		if (!date) return;
		const dateStr = format(date, 'yyyy-MM-dd');
		const params = new URLSearchParams({ date: dateStr });
		if (seriesId) {
			params.append('seriesId', seriesId);
		}
		navigate(`/admin/compose?${params.toString()}`);
		onOpenChange(false);
	};

	const handleEditDevotional = (devotionalId: string) => {
		navigate(`/admin/compose?edit=${devotionalId}`);
		onOpenChange(false);
	};

	const handleViewSeries = (seriesId: string) => {
		navigate(`/series/${seriesId}`);
		onOpenChange(false);
	};

	if (!date) return null;

	const dateStr = format(date, 'EEEE, MMMM d, yyyy');

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
				<DialogHeader>
					<DialogTitle className="flex items-center gap-2">
						<Calendar className="w-5 h-5" />
						{dateStr}
					</DialogTitle>
					<DialogDescription>
						View and manage series and devotionals for this day
					</DialogDescription>
				</DialogHeader>

				{loading ? (
					<div className="space-y-4">
						<Skeleton className="h-32 w-full" />
						<Skeleton className="h-32 w-full" />
					</div>
				) : (
					<div className="space-y-6">
						{/* Action Buttons */}
						<div className="flex gap-2 flex-wrap">
							<Button onClick={handleCreateSeries} variant="default" size="sm">
								<Plus className="w-4 h-4 mr-2" />
								Create New Series
							</Button>
							<Button onClick={() => handleCreateDevotional()} variant="outline" size="sm">
								<Plus className="w-4 h-4 mr-2" />
								Create Devotional
							</Button>
						</div>

						{/* Series Section */}
						{series.length > 0 && (
							<Card>
								<CardHeader>
									<CardTitle className="flex items-center gap-2">
										<BookOpen className="w-5 h-5" />
										Series ({series.length})
									</CardTitle>
								</CardHeader>
								<CardContent>
									<div className="space-y-3">
										{series.map((s) => {
											const seriesDevotionals = devotionals.filter(d => d.series_id === s.id);
											const startsToday = s.start_date && format(new Date(s.start_date), 'yyyy-MM-dd') === format(date, 'yyyy-MM-dd');
											
											return (
												<div
													key={s.id}
													className="p-4 border rounded-lg hover:bg-accent/50 transition-colors"
												>
													<div className="flex items-start justify-between">
														<div className="flex-1">
															<div className="flex items-center gap-2 mb-1">
																<h4 className="font-semibold">{s.name}</h4>
																{startsToday && (
																	<Badge variant="secondary" className="text-xs">
																		Starts Today
																	</Badge>
																)}
															</div>
															{s.description && (
																<p className="text-sm text-muted-foreground mb-2 line-clamp-2">
																	{s.description}
																</p>
															)}
															<div className="flex items-center gap-4 text-xs text-muted-foreground">
																<span>{s.devotionals_count} parts</span>
																{seriesDevotionals.length > 0 && (
																	<span>{seriesDevotionals.length} on this day</span>
																)}
															</div>
														</div>
														<div className="flex gap-2">
															<Button
																variant="ghost"
																size="sm"
																onClick={() => handleViewSeries(s.id)}
															>
																<ExternalLink className="w-4 h-4" />
															</Button>
															<Button
																variant="outline"
																size="sm"
																onClick={() => handleCreateDevotional(s.id)}
															>
																<Plus className="w-4 h-4 mr-1" />
																Add Part
															</Button>
														</div>
													</div>
												</div>
											);
										})}
									</div>
								</CardContent>
							</Card>
						)}

						{/* Devotionals Section */}
						<Card>
							<CardHeader>
								<CardTitle>
									Devotionals ({devotionals.length})
								</CardTitle>
							</CardHeader>
							<CardContent>
								{devotionals.length > 0 ? (
									<div className="space-y-3">
										{devotionals.map((dev) => (
											<div
												key={dev.devotional_id}
												className="p-4 border rounded-lg hover:bg-accent/50 transition-colors"
											>
												<div className="flex items-start justify-between">
													<div className="flex-1">
														<div className="flex items-center gap-2 mb-1">
															<h4 className="font-semibold">{dev.title}</h4>
															<Badge
																variant={
																	dev.status === 'published' ? 'default' :
																	dev.status === 'scheduled' ? 'secondary' : 'outline'
																}
															>
																{dev.status}
															</Badge>
														</div>
														<p className="text-sm text-muted-foreground mb-2">
															By {dev.author_name}
														</p>
														{dev.series_name && (
															<div className="flex items-center gap-2 text-xs">
																<BookOpen className="w-3 h-3" />
																<span className="text-muted-foreground">
																	{dev.series_name}
																	{dev.part_number && ` - Part ${dev.part_number}`}
																</span>
															</div>
														)}
													</div>
													<Button
														variant="ghost"
														size="sm"
														onClick={() => handleEditDevotional(dev.devotional_id)}
													>
														<Edit className="w-4 h-4" />
													</Button>
												</div>
											</div>
										))}
									</div>
								) : (
									<div className="text-center py-8 text-muted-foreground">
										<p>No devotionals scheduled for this day</p>
										<Button
											variant="outline"
											size="sm"
											className="mt-4"
											onClick={() => handleCreateDevotional()}
										>
											<Plus className="w-4 h-4 mr-2" />
											Create Devotional
										</Button>
									</div>
								)}
							</CardContent>
						</Card>
					</div>
				)}
			</DialogContent>
		</Dialog>
	);
}

