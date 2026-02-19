import { useState } from "react";
import {
	DndContext,
	closestCenter,
	KeyboardSensor,
	PointerSensor,
	useSensor,
	useSensors,
	DragEndEvent,
} from "@dnd-kit/core";
import {
	arrayMove,
	SortableContext,
	sortableKeyboardCoordinates,
	verticalListSortingStrategy,
	useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, Eye, Trash2, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
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
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface Devotional {
	id: string;
	title: string;
	part_number: number;
	status: string;
	published_at?: string;
	scheduled_at?: string;
	excerpt?: string;
}

interface SeriesDevotionalsListProps {
	seriesId: string;
	devotionals: Devotional[];
	onReorder: (newOrder: Devotional[]) => void;
	onRemove: (devotionalId: string) => void;
	onPreview?: (devotionalId: string) => void;
}

/**
 * SeriesDevotionalsList - Drag-and-drop list for reordering devotionals in a series
 * Uses @dnd-kit for smooth drag interactions with optimistic updates
 */
export function SeriesDevotionalsList({
	seriesId,
	devotionals,
	onReorder,
	onRemove,
	onPreview,
}: SeriesDevotionalsListProps) {
	const { toast } = useToast();
	const [items, setItems] = useState(devotionals);
	const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
	const [devotionalToRemove, setDevotionalToRemove] = useState<Devotional | null>(null);
	const [isReordering, setIsReordering] = useState(false);

	const sensors = useSensors(
		useSensor(PointerSensor),
		useSensor(KeyboardSensor, {
			coordinateGetter: sortableKeyboardCoordinates,
		})
	);

	const handleDragEnd = async (event: DragEndEvent) => {
		const { active, over } = event;

		if (over && active.id !== over.id) {
			const oldIndex = items.findIndex((item) => item.id === active.id);
			const newIndex = items.findIndex((item) => item.id === over.id);

			const newOrder = arrayMove(items, oldIndex, newIndex);

			// Optimistic update
			setItems(newOrder);
			onReorder(newOrder);

			// Send to backend
			setIsReordering(true);
			try {
				await apiClient.reorderSeriesDevotionals(
					seriesId,
					newOrder.map((d) => d.id)
				);
				toast({
					title: "Success",
					description: "Devotionals reordered successfully",
				});
			} catch (error) {
				console.error("Failed to reorder:", error);
				// Rollback on error
				setItems(devotionals);
				onReorder(devotionals);
				toast({
					title: "Error",
					description: "Failed to reorder devotionals",
					variant: "destructive",
				});
			} finally {
				setIsReordering(false);
			}
		}
	};

	const handleRemove = async () => {
		if (!devotionalToRemove) return;

		try {
			await apiClient.removeDevotionalFromSeries(seriesId, devotionalToRemove.id, true);
			onRemove(devotionalToRemove.id);
			toast({
				title: "Success",
				description: "Devotional removed from series",
			});
		} catch (error) {
			console.error("Failed to remove:", error);
			toast({
				title: "Error",
				description: "Failed to remove devotional",
				variant: "destructive",
			});
		} finally {
			setRemoveDialogOpen(false);
			setDevotionalToRemove(null);
		}
	};

	if (items.length === 0) {
		return (
			<div className="text-center py-12">
				<p className="text-muted-foreground">No devotionals in this series yet.</p>
				<p className="text-sm text-muted-foreground mt-2">
					Add devotionals to the series from the compose page.
				</p>
			</div>
		);
	}

	return (
		<>
			<DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
				<SortableContext items={items.map((d) => d.id)} strategy={verticalListSortingStrategy}>
					<div className="space-y-3">
						{items.map((devotional, index) => (
							<SortableDevotionalItem
								key={devotional.id}
								devotional={devotional}
								index={index}
								isReordering={isReordering}
								onRemove={() => {
									setDevotionalToRemove(devotional);
									setRemoveDialogOpen(true);
								}}
								onPreview={onPreview}
							/>
						))}
					</div>
				</SortableContext>
			</DndContext>

			{/* Remove Confirmation Dialog */}
			<AlertDialog open={removeDialogOpen} onOpenChange={setRemoveDialogOpen}>
				<AlertDialogContent>
					<AlertDialogHeader>
						<AlertDialogTitle>Remove from Series?</AlertDialogTitle>
						<AlertDialogDescription>
							Remove "{devotionalToRemove?.title}" from this series? The devotional
							will not be deleted, just unlinked. Remaining devotionals will be
							renumbered automatically.
						</AlertDialogDescription>
					</AlertDialogHeader>
					<AlertDialogFooter>
						<AlertDialogCancel>Cancel</AlertDialogCancel>
						<AlertDialogAction onClick={handleRemove}>Remove</AlertDialogAction>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialog>
		</>
	);
}

/**
 * SortableDevotionalItem - Single draggable devotional item
 */
function SortableDevotionalItem({
	devotional,
	index,
	isReordering,
	onRemove,
	onPreview,
}: {
	devotional: Devotional;
	index: number;
	isReordering: boolean;
	onRemove: () => void;
	onPreview?: (id: string) => void;
}) {
	const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
		id: devotional.id,
	});

	const style = {
		transform: CSS.Transform.toString(transform),
		transition,
		opacity: isDragging ? 0.5 : 1,
	};

	return (
		<Card ref={setNodeRef} style={style} className={isDragging ? "shadow-lg" : ""}>
			<CardContent className="p-4">
				<div className="flex items-center gap-3">
					{/* Drag Handle */}
					<button
						className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground transition-colors touch-none"
						{...attributes}
						{...listeners}
						disabled={isReordering}
					>
						<GripVertical className="w-5 h-5" />
					</button>

					{/* Part Number */}
					<div className="flex-shrink-0">
						<div className="w-10 h-10 rounded-full bg-secondary/10 flex items-center justify-center">
							<span className="font-bold text-secondary">{index + 1}</span>
						</div>
					</div>

					{/* Content */}
					<div className="flex-1 min-w-0">
						<h4 className="font-semibold text-foreground line-clamp-1 mb-1">
							{devotional.title}
						</h4>
						{devotional.excerpt && (
							<p className="text-sm text-muted-foreground line-clamp-1">
								{devotional.excerpt}
							</p>
						)}
						<div className="flex items-center gap-3 mt-2">
							<Badge
								variant={
									devotional.status === "published"
										? "default"
										: devotional.status === "scheduled"
										? "secondary"
										: "outline"
								}
								className="text-xs"
							>
								{devotional.status}
							</Badge>
							{devotional.scheduled_at && (
								<span className="text-xs text-muted-foreground flex items-center gap-1">
									<Calendar className="w-3 h-3" />
									{new Date(devotional.scheduled_at).toLocaleDateString("en-US", {
										month: "short",
										day: "numeric",
									})}
								</span>
							)}
						</div>
					</div>

					{/* Actions */}
					<div className="flex items-center gap-2 flex-shrink-0">
						{onPreview && (
							<Button
								variant="ghost"
								size="icon"
								onClick={() => onPreview(devotional.id)}
								title="Preview"
							>
								<Eye className="w-4 h-4" />
							</Button>
						)}
						<Button
							variant="ghost"
							size="icon"
							onClick={onRemove}
							className="text-destructive hover:text-destructive"
							title="Remove from series"
						>
							<Trash2 className="w-4 h-4" />
						</Button>
					</div>
				</div>
			</CardContent>
		</Card>
	);
}
