import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
	BookOpen,
	Plus,
	Edit2,
	Trash2,
	Eye,
	Calendar,
	MoreHorizontal,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { SeriesEditorDialog } from "@/components/series/SeriesEditorDialog";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface Series {
	id: string;
	name: string;
	slug: string;
	description?: string;
	cover_image_url?: string;
	author_name: string;
	total_parts: number;
	devotionals_count?: number;
	start_date?: string;
	created_at: string;
	updated_at: string;
}

/**
 * SeriesManagement - Author page for managing their series
 * Allows authors to create, edit, delete, and preview series
 */
export default function SeriesManagement() {
	const navigate = useNavigate();
	const { toast } = useToast();

	const [series, setSeries] = useState<Series[]>([]);
	const [loading, setLoading] = useState(true);
	const [searchQuery, setSearchQuery] = useState("");
	const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
	const [seriesToDelete, setSeriesToDelete] = useState<Series | null>(null);
	const [editorOpen, setEditorOpen] = useState(false);
	const [editingSeriesId, setEditingSeriesId] = useState<string | undefined>(undefined);

	useEffect(() => {
		loadMySeries();
	}, []);

	const loadMySeries = async () => {
		setLoading(true);
		try {
			// Get current user first
			const user = await apiClient.getCurrentUser();
			const response = await apiClient.listSeries(user.id);
			setSeries(response);
		} catch (error) {
			console.error("Failed to load series:", error);
			toast({
				title: "Error",
				description: "Failed to load your series",
				variant: "destructive",
			});
		} finally {
			setLoading(false);
		}
	};

	const handleDelete = async () => {
		if (!seriesToDelete) return;

		try {
			await apiClient.deleteSeries(seriesToDelete.id, "unlink");
			toast({
				title: "Success",
				description: "Series deleted successfully",
			});
			loadMySeries();
		} catch (error) {
			console.error("Failed to delete series:", error);
			toast({
				title: "Error",
				description: "Failed to delete series",
				variant: "destructive",
			});
		} finally {
			setDeleteDialogOpen(false);
			setSeriesToDelete(null);
		}
	};

	const filteredSeries = series.filter((s) =>
		s.name.toLowerCase().includes(searchQuery.toLowerCase())
	);

	return (
		<div className="min-h-screen bg-background">
			<div className="container mx-auto px-4 py-12">
				{/* Header */}
				<div className="flex items-center justify-between mb-8">
					<div>
						<h1 className="font-serif text-3xl md:text-4xl font-bold text-foreground mb-2">
							My Series
						</h1>
						<p className="text-muted-foreground">
							Manage your devotional series collections
						</p>
					</div>

					<Button
						onClick={() => {
							setEditingSeriesId(undefined);
							setEditorOpen(true);
						}}
						size="lg"
						className="gap-2"
					>
						<Plus className="w-5 h-5" />
						New Series
					</Button>
				</div>

				{/* Search */}
				<div className="mb-6">
					<Input
						type="text"
						placeholder="Search series..."
						value={searchQuery}
						onChange={(e) => setSearchQuery(e.target.value)}
						className="max-w-md"
					/>
				</div>

				{/* Series List */}
				{loading ? (
					<div className="space-y-4">
						{Array.from({ length: 3 }).map((_, i) => (
							<Card key={i} className="animate-pulse">
								<CardContent className="p-6">
									<div className="h-6 w-1/3 bg-muted rounded mb-2" />
									<div className="h-4 w-1/2 bg-muted rounded" />
								</CardContent>
							</Card>
						))}
					</div>
				) : filteredSeries.length === 0 ? (
					<EmptyState
						hasSearch={searchQuery.length > 0}
						onCreateNew={() => {
							setEditingSeriesId(undefined);
							setEditorOpen(true);
						}}
					/>
				) : (
					<div className="space-y-4">
						{filteredSeries.map((s, index) => (
							<SeriesListItem
								key={s.id}
								series={s}
								index={index}
								onEdit={() => {
									setEditingSeriesId(s.id);
									setEditorOpen(true);
								}}
								onPreview={() => navigate(`/series/${s.id}`)}
								onDelete={() => {
									setSeriesToDelete(s);
									setDeleteDialogOpen(true);
								}}
							/>
						))}
					</div>
				)}
			</div>

			{/* Series Editor Dialog */}
			<SeriesEditorDialog
				open={editorOpen}
				onOpenChange={setEditorOpen}
				seriesId={editingSeriesId}
				onSuccess={() => {
					loadMySeries();
					setEditorOpen(false);
				}}
			/>

			{/* Delete Confirmation Dialog */}
			<AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>Delete Series?</AlertDialogTitle>
						<AlertDialogDescription>
							Are you sure you want to delete "{seriesToDelete?.name}"? Devotionals in
							this series will be unlinked but not deleted.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Cancel</AlertDialogCancel>
						<AlertDialogAction onClick={handleDelete} className="bg-destructive">
							Delete
						</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</div>
	);
}

/**
 * SeriesListItem - Single series in management list
 */
function SeriesListItem({
	series,
	index,
	onEdit,
	onPreview,
	onDelete,
}: {
	series: Series;
	index: number;
	onEdit: () => void;
	onPreview: () => void;
	onDelete: () => void;
}) {
	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			transition={{ duration: 0.3, delay: index * 0.05 }}
		>
			<Card className="hover:shadow-md transition-shadow">
				<CardContent className="p-6">
					<div className="flex items-start justify-between gap-4">
						{/* Series Info */}
						<div className="flex-1 min-w-0">
							<div className="flex items-start gap-4">
								{/* Cover Image Thumbnail */}
								{series.cover_image_url ? (
									<img
										src={series.cover_image_url}
										alt={series.name}
										className="w-16 h-20 object-cover rounded-lg flex-shrink-0"
									/>
								) : (
									<div className="w-16 h-20 bg-secondary/10 rounded-lg flex items-center justify-center flex-shrink-0">
										<BookOpen className="w-6 h-6 text-secondary/40" />
									</div>
								)}

								{/* Details */}
								<div className="flex-1 min-w-0">
									<h3 className="font-serif text-xl font-bold text-foreground mb-1 line-clamp-1">
										{series.name}
									</h3>

									{series.description && (
										<p className="text-sm text-muted-foreground line-clamp-2 mb-3">
											{series.description}
										</p>
									)}

									<div className="flex items-center gap-3 flex-wrap">
										<Badge variant="secondary" className="gap-1.5">
											<BookOpen className="w-3 h-3" />
											{series.total_parts} {series.total_parts === 1 ? "Part" : "Parts"}
										</Badge>

										{series.start_date && (
											<Badge variant="outline" className="gap-1.5">
												<Calendar className="w-3 h-3" />
												{new Date(series.start_date).toLocaleDateString("en-US", {
													month: "short",
													day: "numeric",
													year: "numeric",
												})}
											</Badge>
										)}
									</div>
								</div>
							</div>
						</div>

						{/* Actions */}
						<div className="flex items-center gap-2 flex-shrink-0">
							<Button variant="outline" size="sm" onClick={onEdit} className="gap-2">
								<Edit2 className="w-4 h-4" />
								Edit
							</Button>

							<Button variant="outline" size="sm" onClick={onPreview} className="gap-2">
								<Eye className="w-4 h-4" />
								Preview
							</Button>

							<DropdownMenu>
								<DropdownMenuTrigger asChild>
									<Button variant="ghost" size="icon">
										<MoreHorizontal className="w-4 h-4" />
									</Button>
								</DropdownMenuTrigger>
								<DropdownMenuContent align="end">
									<DropdownMenuItem onClick={onDelete} className="text-destructive">
										<Trash2 className="w-4 h-4 mr-2" />
										Delete
									</DropdownMenuItem>
								</DropdownMenuContent>
							</DropdownMenu>
						</div>
					</div>
				</CardContent>
			</Card>
		</motion.div>
	);
}

/**
 * EmptyState - Display when no series exist
 */
function EmptyState({
	hasSearch,
	onCreateNew,
}: {
	hasSearch: boolean;
	onCreateNew: () => void;
}) {
	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="text-center py-20"
		>
			<div className="w-20 h-20 mx-auto mb-6 rounded-full bg-secondary/10 flex items-center justify-center">
				<BookOpen className="w-10 h-10 text-secondary" />
			</div>

			<h3 className="font-serif text-2xl font-bold text-foreground mb-3">
				{hasSearch ? "No series found" : "Start Your First Series"}
			</h3>

			<p className="text-muted-foreground mb-6 max-w-md mx-auto">
				{hasSearch
					? "Try a different search term"
					: "Create a series to organize your devotionals into multi-day spiritual journeys"}
			</p>

			{!hasSearch && (
				<Button onClick={onCreateNew} size="lg" className="gap-2">
					<Plus className="w-5 h-5" />
					Create Series
				</Button>
			)}
		</motion.div>
	);
}
