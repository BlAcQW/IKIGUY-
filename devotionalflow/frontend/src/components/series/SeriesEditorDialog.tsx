import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, Calendar, Image, Save, X } from "lucide-react";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { SeriesDevotionalsList } from "./SeriesDevotionalsList";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { ImageSearchDialog } from "@/components/media/ImageSearchDialog";

interface Series {
	id?: string;
	name: string;
	description?: string;
	cover_image_url?: string;
	start_date?: string;
}

interface Devotional {
	id: string;
	title: string;
	part_number: number;
	status: string;
	published_at?: string;
	scheduled_at?: string;
	excerpt?: string;
}

interface SeriesEditorDialogProps {
	open: boolean;
	onOpenChange: (open: boolean) => void;
	seriesId?: string; // If editing existing series
	onSuccess?: () => void;
}

/**
 * SeriesEditorDialog - Modal dialog for creating/editing series
 * Features tabs for Details and Devotionals management
 */
export function SeriesEditorDialog({
	open,
	onOpenChange,
	seriesId,
	onSuccess,
}: SeriesEditorDialogProps) {
	const { toast } = useToast();
	const navigate = useNavigate();
	const [activeTab, setActiveTab] = useState("details");
	const [loading, setLoading] = useState(false);
	const [saving, setSaving] = useState(false);
	const [showImagePicker, setShowImagePicker] = useState(false);
	const [isUploadingImage, setIsUploadingImage] = useState(false);
	const imageInputRef = useRef<HTMLInputElement>(null);

	// Form state
	const [name, setName] = useState("");
	const [description, setDescription] = useState("");
	const [coverImageUrl, setCoverImageUrl] = useState("");
	const [startDate, setStartDate] = useState("");
	const [numberOfParts, setNumberOfParts] = useState<number | "">("");

	// Devotionals
	const [devotionals, setDevotionals] = useState<Devotional[]>([]);

	useEffect(() => {
		if (open && seriesId) {
			loadSeries();
		} else if (open && !seriesId) {
			// Reset form for new series
			setName("");
			setDescription("");
			setCoverImageUrl("");
			setStartDate("");
			setNumberOfParts("");
			setDevotionals([]);
		}
	}, [open, seriesId]);

	const loadSeries = async () => {
		if (!seriesId) return;

		setLoading(true);
		try {
			const [seriesData, devotionalsData] = await Promise.all([
				apiClient.getSeries(seriesId),
				apiClient.getSeriesDevotionals(seriesId),
			]);

			setName(seriesData.name);
			setDescription(seriesData.description || "");
			setCoverImageUrl(seriesData.cover_image_url || "");
			setStartDate(
				seriesData.start_date
					? new Date(seriesData.start_date).toISOString().split("T")[0]
					: ""
			);
			setDevotionals(devotionalsData);
		} catch (error) {
			console.error("Failed to load series:", error);
			toast({
				title: "Error",
				description: "Failed to load series details",
				variant: "destructive",
			});
		} finally {
			setLoading(false);
		}
	};

	const handleSave = async () => {
		if (!name.trim()) {
			toast({
				title: "Validation Error",
				description: "Series name is required",
				variant: "destructive",
			});
			return;
		}

		setSaving(true);
		try {
			const seriesData = {
				name: name.trim(),
				description: description.trim() || undefined,
				cover_image_url: coverImageUrl.trim() || undefined,
				start_date: startDate || undefined,
			};

			if (seriesId) {
				// Update existing
				await apiClient.updateSeries(seriesId, seriesData);
				toast({
					title: "Success",
					description: "Series updated successfully",
				});
			} else {
				// Create new
				const created = await apiClient.createSeries(seriesData);
				toast({
					title: "Success",
					description: "Series created successfully",
				});
				// Navigate to edit mode
				navigate(`/dashboard/series/${created.id}/edit`);
			}

			onSuccess?.();
			onOpenChange(false);
		} catch (error) {
			console.error("Failed to save series:", error);
			toast({
				title: "Error",
				description: "Failed to save series",
				variant: "destructive",
			});
		} finally {
			setSaving(false);
		}
	};

	const handleImageSelect = (url: string) => {
		setCoverImageUrl(url);
		setShowImagePicker(false);
	};

	const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
		const file = e.target.files?.[0];
		if (!file) return;

		// Validate file type
		if (!file.type.startsWith("image/")) {
			toast({
				title: "Invalid file type",
				description: "Please select an image file (JPG, PNG, GIF, WebP)",
				variant: "destructive",
			});
			return;
		}

		// Validate file size (10MB max)
		const maxSize = 10 * 1024 * 1024; // 10MB
		if (file.size > maxSize) {
			toast({
				title: "File too large",
				description: "Image must be smaller than 10MB",
				variant: "destructive",
			});
			return;
		}

		setIsUploadingImage(true);
		try {
			const formData = new FormData();
			formData.append("file", file);
			formData.append("category", "series-covers");

			const response = await apiClient.client.post("/media/upload-image", formData, {
				headers: {
					'Content-Type': 'multipart/form-data'
				}
			});

			setCoverImageUrl(response.data.url);
			toast({
				title: "Image uploaded",
				description: "Cover image has been uploaded successfully",
			});
		} catch (error: any) {
			console.error("Image upload failed:", error);
			toast({
				title: "Upload failed",
				description: error.response?.data?.detail || "Failed to upload image",
				variant: "destructive",
			});
		} finally {
			setIsUploadingImage(false);
		}
	};

	const handleSchedule = async () => {
		if (!seriesId) {
			toast({
				title: "Info",
				description: "Save the series first before scheduling",
			});
			return;
		}

		if (!startDate) {
			toast({
				title: "Validation Error",
				description: "Please set a start date before scheduling",
				variant: "destructive",
			});
			return;
		}

		try {
			const result = await apiClient.scheduleSeries(seriesId);
			toast({
				title: "Success",
				description: `Scheduled ${result.scheduled_count} devotional(s)`,
			});
			// Reload devotionals
			loadSeries();
		} catch (error) {
			console.error("Failed to schedule series:", error);
			toast({
				title: "Error",
				description: "Failed to schedule devotionals",
				variant: "destructive",
			});
		}
	};

	return (
		<Dialog open={open} onOpenChange={onOpenChange}>
			<DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
				<DialogHeader>
					<DialogTitle>
						{seriesId ? "Edit Series" : "Create New Series"}
					</DialogTitle>
					<DialogDescription>
						{seriesId
							? "Update series details and manage devotionals"
							: "Create a new devotional series collection"}
					</DialogDescription>
				</DialogHeader>

				{loading ? (
					<div className="flex items-center justify-center py-12">
						<div className="text-muted-foreground">Loading...</div>
					</div>
				) : (
					<Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col overflow-hidden">
						<TabsList className="grid w-full grid-cols-2">
							<TabsTrigger value="details">
								<BookOpen className="w-4 h-4 mr-2" />
								Details
							</TabsTrigger>
							<TabsTrigger value="devotionals" disabled={!seriesId}>
								<Calendar className="w-4 h-4 mr-2" />
								Devotionals {devotionals.length > 0 && `(${devotionals.length})`}
							</TabsTrigger>
						</TabsList>

						<div className="flex-1 overflow-y-auto mt-4">
							{/* Details Tab */}
							<TabsContent value="details" className="space-y-4 mt-0">
								<div className="space-y-4">
									{/* Name */}
									<div className="space-y-2">
										<Label htmlFor="name">Series Name *</Label>
										<Input
											id="name"
											value={name}
											onChange={(e) => setName(e.target.value)}
											placeholder="e.g., 30 Days of Prayer"
											required
										/>
									</div>

									{/* Description */}
									<div className="space-y-2">
										<Label htmlFor="description">Description</Label>
										<Textarea
											id="description"
											value={description}
											onChange={(e) => setDescription(e.target.value)}
											placeholder="Describe what this series is about..."
											rows={4}
										/>
									</div>

									{/* Cover Image URL */}
									<div className="space-y-2">
										<Label htmlFor="cover_image_url">Cover Image URL</Label>
										<div className="flex gap-2">
											<Input
												id="cover_image_url"
												value={coverImageUrl}
												onChange={(e) => setCoverImageUrl(e.target.value)}
												placeholder="https://example.com/image.jpg"
											/>
											<Button
												variant="outline"
												size="icon"
												onClick={() => setShowImagePicker(true)}
												disabled={isUploadingImage}
											>
												<Image className="w-4 h-4" />
											</Button>
											<input
												type="file"
												ref={imageInputRef}
												accept="image/*"
												className="hidden"
												onChange={handleImageUpload}
											/>
										</div>
										{coverImageUrl && (
											<img
												src={coverImageUrl}
												alt="Cover preview"
												className="w-full h-48 object-cover rounded-lg mt-2"
											/>
										)}
									</div>

									{/* Number of Parts (for new series) */}
									{!seriesId && (
										<div className="space-y-2">
											<Label htmlFor="number_of_parts">Number of Parts (Optional)</Label>
											<Input
												id="number_of_parts"
												type="number"
												min="2"
												value={numberOfParts}
												onChange={(e) => {
													const val = e.target.value;
													setNumberOfParts(val === "" ? "" : parseInt(val) || "");
												}}
												placeholder="e.g., 3 (for a 3-part series)"
											/>
											<p className="text-xs text-muted-foreground">
												Specify how many devotionals this series will contain. You can add more devotionals later to extend the series.
											</p>
										</div>
									)}

									{/* Start Date */}
									<div className="space-y-2">
										<Label htmlFor="start_date">Start Date</Label>
										<Input
											id="start_date"
											type="date"
											value={startDate}
											onChange={(e) => setStartDate(e.target.value)}
										/>
										<p className="text-xs text-muted-foreground">
											When set, devotionals will be auto-scheduled daily starting from this
											date
										</p>
									</div>
								</div>
							</TabsContent>

							{/* Devotionals Tab */}
							<TabsContent value="devotionals" className="mt-0">
								<div className="space-y-4">
									{seriesId && startDate && (
										<div className="flex items-center justify-between p-4 bg-muted rounded-lg">
											<div>
												<p className="font-medium">Auto-Schedule Devotionals</p>
												<p className="text-sm text-muted-foreground">
													Schedule all devotionals based on start date and part numbers
												</p>
											</div>
											<Button onClick={handleSchedule} variant="secondary">
												Schedule Now
											</Button>
										</div>
									)}

									<SeriesDevotionalsList
										seriesId={seriesId!}
										devotionals={devotionals}
										onReorder={(newOrder) => setDevotionals(newOrder)}
										onRemove={(id) => {
											setDevotionals(devotionals.filter((d) => d.id !== id));
										}}
										onPreview={(id) => {
											window.open(`/devotional/${id}`, "_blank");
										}}
									/>
								</div>
							</TabsContent>
						</div>
					</Tabs>
				)}

				<DialogFooter>
					<Button variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
						Cancel
					</Button>
					<Button onClick={handleSave} disabled={saving || loading}>
						{saving ? (
							"Saving..."
						) : (
							<>
								<Save className="w-4 h-4 mr-2" />
								{seriesId ? "Save Changes" : "Create Series"}
							</>
						)}
					</Button>
				</DialogFooter>
			</DialogContent>

			{/* Image Picker Dialog */}
			<ImageSearchDialog
				open={showImagePicker}
				onClose={() => setShowImagePicker(false)}
				onSelectImage={handleImageSelect}
			/>
		</Dialog>
	);
}
