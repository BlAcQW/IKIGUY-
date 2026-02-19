import { useState, useRef, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { format, startOfYear, differenceInDays, isLeapYear } from "date-fns";
import {
	BookOpen,
	Bold,
	Italic,
	List,
	Quote,
	Image,
	Mic,
	Video,
	Calendar,
	Tag,
	Save,
	Send,
	ArrowLeft,
	Sparkles,
	X,
	Upload,
	Loader2,
	Plus,
	Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/api";
import { ScriptureAutocomplete } from "@/components/scripture/ScriptureAutocomplete";
import { BibleVersionCombobox } from "@/components/scripture/BibleVersionCombobox";
import { DateTimePicker } from "@/components/ui/date-time-picker";
import { ImageSearchDialog } from "@/components/media/ImageSearchDialog";
import { SeriesCombobox } from "@/components/ui/series-combobox";
import { DevotionalPreview } from "@/components/compose/DevotionalPreview";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const categories = [
	"Faith",
	"Purpose",
	"Prayer",
	"Wisdom",
	"Love",
	"Hope",
	"Gratitude",
	"Forgiveness",
];

const bibleTranslations = [
	// Modern Readable Translations (19 English Bibles via API.Bible)
	{ id: "bsb", name: "Berean Standard Bible (BSB)" },
	{ id: "cev", name: "Contemporary English Version (CEV)" },
	{ id: "fbv", name: "Free Bible Version (FBV)" },
	{ id: "t4t", name: "Translation for Translators (T4T)" },


	// Classic Translations
	{ id: "kjv", name: "King James Version (KJV)" },
	{ id: "kjvcpb", name: "Cambridge Paragraph Bible of the KJV" },
	{ id: "gnv", name: "Geneva Bible (1599)" },
	{ id: "asv", name: "American Standard Version (ASV)" },
	{ id: "rv", name: "Revised Version 1885 (RV)" },
	{ id: "dra", name: "Douay-Rheims American 1899 (DRA)" },

	// Literal & Scholarly Translations
	{ id: "lsv", name: "Literal Standard Version (LSV)" },
	{ id: "tcent", name: "Text-Critical English New Testament (TCENT)" },
	{ id: "f35", name: "English New Testament According to Family 35" },

	// World English Bible Family
	{ id: "web", name: "World English Bible (WEB)" },
	{ id: "webbe", name: "World English Bible, British Edition (WEBBE)" },
	{ id: "webu", name: "World English Bible Updated (WEBU)" },
	{ id: "webus", name: "World English Bible, American English (WEBUS)" },

	// Contemporary English Version Variants
	{ id: "cevdci", name: "CEV Interconfessional Edition (CEVDCI)" },
	{ id: "cevdco", name: "CEV Old Tradition (CEVDCO)" },
];

// Helper function to calculate day of year (1-365 or 1-366)
const getDayOfYear = (date: Date): { day: number; totalDays: number } => {
	const year = date.getFullYear();
	const start = startOfYear(date);
	const day = differenceInDays(date, start) + 1;
	const totalDays = isLeapYear(date) ? 366 : 365;
	return { day, totalDays };
};

const Compose = () => {
	const navigate = useNavigate();
	const { toast } = useToast();
	const [searchParams] = useSearchParams();
	const editId = searchParams.get('edit');
	const dateParam = searchParams.get('date');
	const seriesIdParam = searchParams.get('seriesId');
	const createSeriesParam = searchParams.get('createSeries');
	const [isLoadingDevotional, setIsLoadingDevotional] = useState(false);
	const [title, setTitle] = useState("");
	const [content, setContent] = useState("");
	const [prayer, setPrayer] = useState("");
	const [reflection, setReflection] = useState("");
	const [otherBibleReferences, setOtherBibleReferences] = useState("");
	const [scripture, setScripture] = useState("");
	const [selectedTranslation, setSelectedTranslation] = useState("de4e12af7f28f599-01"); // KJV Bible ID
	const [bibleTranslationsList, setBibleTranslationsList] = useState(bibleTranslations);
	const [isLoadingBibles, setIsLoadingBibles] = useState(false);
	const [scriptureReferences, setScriptureReferences] = useState<Array<{ text: string, reference: string, translation_name: string }>>([]);
	const [isLookingUpScripture, setIsLookingUpScripture] = useState(false);
	const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
	const [isScheduling, setIsScheduling] = useState(false);
	const [scheduleDate, setScheduleDate] = useState<Date | undefined>(undefined);

	// Calculate day of year based on schedule date or current date
	const dayOfYear = useMemo(() => {
		const dateToUse = scheduleDate || new Date();
		return getDayOfYear(dateToUse);
	}, [scheduleDate]);

	// Series state
	const [isPartOfSeries, setIsPartOfSeries] = useState(false);
	const [selectedSeriesId, setSelectedSeriesId] = useState<string | null>(null);
	const [newSeriesName, setNewSeriesName] = useState("");
	const [partNumber, setPartNumber] = useState<number>(1);
	const [availableSeries, setAvailableSeries] = useState<Array<{ id: string, name: string }>>([]);
	const [isLoadingSeries, setIsLoadingSeries] = useState(false);

	// Image upload state
	const [coverImage, setCoverImage] = useState<string | null>(null);
	const [coverImageFile, setCoverImageFile] = useState<File | null>(null);
	const [isUploadingImage, setIsUploadingImage] = useState(false);
	const [isImageSearchOpen, setIsImageSearchOpen] = useState(false);
	const [imageAttribution, setImageAttribution] = useState<{ photographer: string; url: string } | null>(null);
	const imageInputRef = useRef<HTMLInputElement>(null);

	// Preview state
	const [isPreviewOpen, setIsPreviewOpen] = useState(false);

	// Fetch available Bible translations on mount
	useEffect(() => {
		const fetchBibles = async () => {
			setIsLoadingBibles(true);
			try {
				const response = await apiClient.client.get('/ai/bibles/available?language=eng');
				const bibles = response.data.map((bible: any) => ({
					id: bible.id,
					name: `${bible.name} (${bible.abbreviation})`,
				}));
				setBibleTranslationsList(bibles);
			} catch (error) {
				console.error('Failed to fetch Bible translations:', error);
				// Keep using hardcoded list as fallback
			} finally {
				setIsLoadingBibles(false);
			}
		};

		fetchBibles();
	}, []);

	// Fetch available series on mount
	useEffect(() => {
		const fetchSeries = async () => {
			setIsLoadingSeries(true);
			try {
				const series = await apiClient.listSeries();
				setAvailableSeries(series.map((s: any) => ({ id: s.id, name: s.name })));
			} catch (error) {
				console.error('Failed to fetch series:', error);
			} finally {
				setIsLoadingSeries(false);
			}
		};

		fetchSeries();
	}, []);

	// Handle date and seriesId query parameters
	useEffect(() => {
		if (dateParam) {
			try {
				const date = new Date(dateParam);
				if (!isNaN(date.getTime())) {
					setIsScheduling(true);
					// Set time to 8 AM
					date.setHours(8, 0, 0, 0);
					setScheduleDate(date);
				}
			} catch (error) {
				console.error('Invalid date parameter:', error);
			}
		}

		if (seriesIdParam) {
			setIsPartOfSeries(true);
			setSelectedSeriesId(seriesIdParam);
			// Fetch series to get the next part number
			const fetchSeriesInfo = async () => {
				try {
					const series = await apiClient.getSeries(seriesIdParam);
					if (series && series.devotionals) {
						// Find the highest part number and add 1
						const maxPart = Math.max(
							...series.devotionals.map((d: any) => d.part_number || 0),
							0
						);
						setPartNumber(maxPart + 1);
					}
				} catch (error) {
					console.error('Failed to fetch series info:', error);
				}
			};
			fetchSeriesInfo();
		}

		if (createSeriesParam === 'true') {
			setIsPartOfSeries(true);
			setSelectedSeriesId(null);
			setNewSeriesName("");
			setPartNumber(1);
		}
	}, [dateParam, seriesIdParam, createSeriesParam]);

	// Load devotional data when in edit mode
	useEffect(() => {
		if (!editId) return;

		const loadDevotional = async () => {
			setIsLoadingDevotional(true);
			try {
				const devotional = await apiClient.getDevotional(editId);

				// Set basic fields
				setTitle(devotional.title || "");
				setSelectedCategories(devotional.categories || []);
				setCoverImage(devotional.cover_image_url || null);

				// Parse content blocks
				if (devotional.content && Array.isArray(devotional.content)) {
					devotional.content.forEach((block: any) => {
						switch (block.type) {
							case 'paragraph':
								// Combine all paragraph blocks into content
								setContent(prev => prev ? `${prev}\n\n${block.text}` : block.text);
								break;
							case 'scripture':
								// Add to scripture references
								setScriptureReferences(prev => [...prev, {
									text: block.text,
									reference: block.scripture_reference || '',
									translation_name: block.translation || 'KJV'
								}]);
								break;
							case 'prayer':
								setPrayer(block.text || "");
								break;
							case 'reflection':
								setReflection(block.text || "");
								break;
							case 'other_bible_references':
								setOtherBibleReferences(block.text || "");
								break;
						}
					});
				}

				// Set schedule if exists
				if (devotional.scheduled_at) {
					setIsScheduling(true);
					setScheduleDate(new Date(devotional.scheduled_at));
				}

				// Set series data if exists
				if (devotional.series_id) {
					setIsPartOfSeries(true);
					setSelectedSeriesId(devotional.series_id);
					setPartNumber(devotional.part_number || 1);
				}

				toast({
					title: "Devotional loaded",
					description: "Ready to edit your devotional",
				});
			} catch (error: any) {
				console.error('Failed to load devotional:', error);
				toast({
					title: "Load failed",
					description: error.response?.data?.detail || "Failed to load devotional",
					variant: "destructive",
				});
			} finally {
				setIsLoadingDevotional(false);
			}
		};

		loadDevotional();
	}, [editId, toast]);

	const toggleCategory = (category: string) => {
		setSelectedCategories((prev) =>
			prev.includes(category)
				? prev.filter((c) => c !== category)
				: [...prev, category]
		);
	};

	const handleImageClick = () => {
		imageInputRef.current?.click();
	};

	const handleImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
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

		// Show preview
		const reader = new FileReader();
		reader.onload = (e) => {
			setCoverImage(e.target?.result as string);
		};
		reader.readAsDataURL(file);

		// Upload to server
		setIsUploadingImage(true);
		try {
			const formData = new FormData();
			formData.append("file", file);
			formData.append("category", "devotional-covers");

			// Set Content-Type to multipart/form-data for file upload
			const response = await apiClient.client.post("/media/upload-image", formData, {
				headers: {
					'Content-Type': 'multipart/form-data'
				}
			});

			setCoverImageFile(file);
			toast({
				title: "Image uploaded",
				description: "Cover image has been uploaded successfully",
			});
		} catch (error: any) {
			console.error("Image upload failed:", error);
			setCoverImage(null);
			toast({
				title: "Upload failed",
				description: error.response?.data?.detail || "Failed to upload image",
				variant: "destructive",
			});
		} finally {
			setIsUploadingImage(false);
		}
	};

	const handleRemoveImage = () => {
		setCoverImage(null);
		setCoverImageFile(null);
		setImageAttribution(null);
		if (imageInputRef.current) {
			imageInputRef.current.value = "";
		}
	};

	const handleSelectStockPhoto = (imageUrl: string, attribution?: { photographer: string; url: string }) => {
		setCoverImage(imageUrl);
		setCoverImageFile(null); // Clear file since we're using a URL
		if (attribution) {
			setImageAttribution(attribution);
		}
	};

	const handleLookupScripture = async () => {
		if (!scripture.trim()) {
			toast({
				title: "No reference entered",
				description: "Please enter a scripture reference (e.g., John 3:16)",
				variant: "destructive",
			});
			return;
		}

		// Check if reference already exists
		const existingRef = scriptureReferences.find(
			ref => ref.reference.toLowerCase() === scripture.trim().toLowerCase()
		);
		if (existingRef) {
			toast({
				title: "Reference already added",
				description: `${existingRef.reference} is already in your list`,
				variant: "destructive",
			});
			return;
		}

		setIsLookingUpScripture(true);
		try {
			const url = `/ai/scriptures/${encodeURIComponent(scripture)}?translation=${selectedTranslation}`;
			const response = await apiClient.client.get(url);
			setScriptureReferences([...scriptureReferences, response.data]);
			setScripture(""); // Clear input after adding
			toast({
				title: "Scripture added",
				description: `Added ${response.data.reference} (${response.data.translation_name})`,
			});
		} catch (error: any) {
			console.error("Scripture lookup failed:", error);
			toast({
				title: "Scripture not found",
				description: error.response?.data?.detail || "Could not find that scripture reference. Please check the format (e.g., John 3:16)",
				variant: "destructive",
			});
		} finally {
			setIsLookingUpScripture(false);
		}
	};

	const handleRemoveScripture = (index: number) => {
		setScriptureReferences(scriptureReferences.filter((_, i) => i !== index));
	};

	const handleSaveDraft = async () => {
		if (!title.trim()) {
			toast({
				title: "Title required",
				description: "Please add a title for your devotional.",
				variant: "destructive",
			});
			return;
		}

		try {
			const devotionalData: any = {
				title: title.trim(),
				content: [
					{ type: "paragraph", text: content.trim() },
					...scriptureReferences.map(ref => ({
						type: "scripture",
						text: ref.text,
						scripture_reference: ref.reference,
						translation: ref.translation_name
					})),
					...(reflection.trim() ? [{ type: "reflection", text: reflection.trim() }] : []),
					...(prayer.trim() ? [{ type: "prayer", text: prayer.trim() }] : []),
					...(otherBibleReferences.trim() ? [{ type: "other_bible_references", text: otherBibleReferences.trim() }] : []),
				],
				categories: selectedCategories,
				cover_image_url: coverImage || undefined,
				status: "draft",
			};

			// Add series fields if part of series
			if (isPartOfSeries) {
				if (selectedSeriesId) {
					devotionalData.series_id = selectedSeriesId;
				} else if (newSeriesName.trim()) {
					devotionalData.series_name = newSeriesName.trim();
				}
				devotionalData.part_number = partNumber;
			}

			if (editId) {
				// Update existing devotional
				await apiClient.client.put(`/devotionals/${editId}`, devotionalData);
				toast({
					title: "Draft updated",
					description: "Your changes have been saved.",
				});
			} else {
				// Create new devotional
				await apiClient.client.post('/devotionals', devotionalData);
				toast({
					title: "Draft saved",
					description: "Your devotional has been saved as a draft.",
				});
			}
			navigate("/admin/content");
		} catch (error: any) {
			console.error('Failed to save draft:', error);
			toast({
				title: "Save failed",
				description: error.response?.data?.detail || "Failed to save devotional",
				variant: "destructive",
			});
		}
	};

	const handlePublish = async () => {
		if (!title.trim() || !content.trim()) {
			toast({
				title: "Missing content",
				description: "Please add a title and content before publishing.",
				variant: "destructive",
			});
			return;
		}

		if (isScheduling && !scheduleDate) {
			toast({
				title: "Schedule date required",
				description: "Please select a date and time for scheduled publication.",
				variant: "destructive",
			});
			return;
		}

		try {
			const devotionalData: any = {
				title: title.trim(),
				content: [
					{ type: "paragraph", text: content.trim() },
					...scriptureReferences.map(ref => ({
						type: "scripture",
						text: ref.text,
						scripture_reference: ref.reference,
						translation: ref.translation_name
					})),
					...(reflection.trim() ? [{ type: "reflection", text: reflection.trim() }] : []),
					...(prayer.trim() ? [{ type: "prayer", text: prayer.trim() }] : []),
					...(otherBibleReferences.trim() ? [{ type: "other_bible_references", text: otherBibleReferences.trim() }] : []),
				],
				categories: selectedCategories,
				cover_image_url: coverImage || undefined,
				status: isScheduling ? "scheduled" : "published",
				scheduled_at: isScheduling && scheduleDate ? scheduleDate.toISOString() : undefined,
			};

			// Add series fields if part of series
			if (isPartOfSeries) {
				if (selectedSeriesId) {
					devotionalData.series_id = selectedSeriesId;
				} else if (newSeriesName.trim()) {
					devotionalData.series_name = newSeriesName.trim();
				}
				devotionalData.part_number = partNumber;
			}

			if (editId) {
				// Update existing devotional
				await apiClient.client.put(`/devotionals/${editId}`, devotionalData);
				toast({
					title: isScheduling ? "Devotional updated" : "Devotional updated!",
					description: isScheduling
						? `Your devotional will be published on ${format(scheduleDate!, "PPP 'at' h:mm a")}`
						: "Your devotional has been updated and is live.",
				});
			} else {
				// Create new devotional
				await apiClient.client.post('/devotionals', devotionalData);
				const formattedDate = scheduleDate
					? format(scheduleDate, "PPP 'at' h:mm a")
					: "";
				toast({
					title: isScheduling ? "Devotional scheduled" : "Devotional published!",
					description: isScheduling
						? `Your devotional will be published on ${formattedDate}`
						: "Your devotional is now live for readers.",
				});
			}
			navigate("/admin/content");
		} catch (error: any) {
			console.error('Failed to publish devotional:', error);
			
			// Extract error message from validation errors
			let errorMessage = "Failed to publish devotional";
			if (error.response?.data) {
				if (typeof error.response.data.detail === 'string') {
					errorMessage = error.response.data.detail;
				} else if (Array.isArray(error.response.data.detail)) {
					// Handle validation errors array
					const errors = error.response.data.detail.map((err: any) => {
						if (typeof err === 'string') return err;
						if (err.msg) return `${err.loc?.join('.') || 'field'}: ${err.msg}`;
						return JSON.stringify(err);
					}).join(', ');
					errorMessage = errors || errorMessage;
				} else if (error.response.data.detail) {
					errorMessage = JSON.stringify(error.response.data.detail);
				}
			}
			
			toast({
				title: "Publish failed",
				description: errorMessage,
				variant: "destructive",
			});
		}
	};

	return (
		<div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
			{/* Header */}
			<header className="sticky top-0 z-10 bg-background/80 backdrop-blur-md border-b border-border/50 shadow-sm">
				<div className="flex items-center justify-between px-4 md:px-6 h-16">
					<div className="flex items-center gap-4">
						<Button
							variant="ghost"
							size="icon"
							onClick={() => navigate("/admin/content")}
						>
							<ArrowLeft className="w-5 h-5" />
						</Button>
						<div className="flex items-center gap-2">
							<div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
								<BookOpen className="w-4 h-4 text-secondary-foreground" />
							</div>
							<span className="font-serif text-lg font-semibold text-foreground hidden sm:block">
								{isLoadingDevotional ? "Loading..." : editId ? "Edit Devotional" : "New Devotional"}
							</span>
						</div>
					</div>
					<div className="flex items-center gap-2">
						<Button 
							variant="outline" 
							size="sm" 
							onClick={() => setIsPreviewOpen(true)}
							className="hover:bg-secondary/10 hover:border-secondary/50 transition-all"
						>
							<Eye className="w-4 h-4 mr-2" />
							<span className="hidden sm:inline">Preview</span>
						</Button>
						<Button 
							variant="ghost" 
							size="sm" 
							onClick={handleSaveDraft} 
							disabled={isLoadingDevotional}
							className="hover:bg-muted/80 transition-all"
						>
							<Save className="w-4 h-4 mr-2" />
							<span className="hidden sm:inline">{editId ? "Save Changes" : "Save Draft"}</span>
						</Button>
						<Button 
							variant="hero" 
							size="sm" 
							onClick={handlePublish} 
							disabled={isLoadingDevotional}
							className="shadow-md hover:shadow-lg transition-all"
						>
							<Send className="w-4 h-4 mr-2" />
							{editId ? (isScheduling ? "Update Schedule" : "Update") : (isScheduling ? "Schedule" : "Publish")}
						</Button>
					</div>
				</div>
			</header>

			<div className="max-w-4xl mx-auto p-4 md:p-6">
				<motion.div
					initial={{ opacity: 0, y: 20 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ duration: 0.5 }}
					className="space-y-4"
				>
					{/* Series */}
					<div className="group relative bg-gradient-to-br from-card to-card/50 rounded-xl border border-border/50 p-4 shadow-sm hover:shadow-md transition-all duration-300 backdrop-blur-sm">
						<div className="absolute inset-0 bg-gradient-to-br from-secondary/5 via-transparent to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
						<div className="relative flex items-center justify-between mb-3">
							<div className="flex items-center gap-2">
								<div className="p-1.5 rounded-lg bg-secondary/10 group-hover:bg-secondary/20 transition-colors">
									<BookOpen className="w-3.5 h-3.5 text-secondary" />
								</div>
								<div>
									<Label className="text-sm font-semibold text-foreground">
										Part of Series
									</Label>
									<p className="text-xs text-muted-foreground mt-0.5">Organize devotionals into a series</p>
								</div>
							</div>
							<button
								onClick={() => setIsPartOfSeries(!isPartOfSeries)}
								className={`relative w-14 h-7 rounded-full transition-all duration-300 ${isPartOfSeries 
									? "bg-secondary shadow-lg shadow-secondary/30" 
									: "bg-muted hover:bg-muted/80"
								}`}
							>
								<span
									className={`absolute top-0.5 w-6 h-6 rounded-full bg-background shadow-lg transition-all duration-300 ${isPartOfSeries ? "left-7 translate-x-0" : "left-0.5"
									}`}
								/>
							</button>
						</div>
						{isPartOfSeries && (
							<motion.div
								initial={{ opacity: 0, height: 0 }}
								animate={{ opacity: 1, height: "auto" }}
								className="space-y-3 mt-3"
							>
								<div>
									<Label className="text-xs font-medium text-foreground mb-2 block">
										Select Existing Series or Create New
									</Label>
									<SeriesCombobox
										series={availableSeries}
										value={selectedSeriesId}
										onValueChange={(value) => {
											setSelectedSeriesId(value);
											if (value) {
												setNewSeriesName("");
											}
										}}
										placeholder="Select series or create new..."
										isLoading={isLoadingSeries}
									/>
								</div>
								{selectedSeriesId ? (
									<div>
										<Label className="text-xs font-medium text-foreground mb-2 block">
											Part Number
										</Label>
										<Input
											type="number"
											min="1"
											value={partNumber}
											onChange={(e) => setPartNumber(parseInt(e.target.value) || 1)}
											placeholder="1"
											className="border-border/50 focus:border-secondary/50 focus:ring-2 focus:ring-secondary/20 transition-all"
										/>
									</div>
								) : (
									<>
										<div>
											<Label className="text-xs font-medium text-foreground mb-2 block">
												Series Name
											</Label>
											<Input
												value={newSeriesName}
												onChange={(e) => setNewSeriesName(e.target.value)}
												placeholder="Enter series name (e.g., 'Walking in Faith')"
												className="border-border/50 focus:border-secondary/50 focus:ring-2 focus:ring-secondary/20 transition-all"
											/>
										</div>
										<div>
											<Label className="text-xs font-medium text-foreground mb-2 block">
												Part Number
											</Label>
											<Input
												type="number"
												min="1"
												value={partNumber}
												onChange={(e) => setPartNumber(parseInt(e.target.value) || 1)}
												placeholder="1"
												className="border-border/50 focus:border-secondary/50 focus:ring-2 focus:ring-secondary/20 transition-all"
											/>
										</div>
									</>
								)}
							</motion.div>
						)}
					</div>

					{/* Schedule */}
					<div className="group relative bg-gradient-to-br from-card to-card/50 rounded-xl border border-border/50 p-4 shadow-sm hover:shadow-md transition-all duration-300 backdrop-blur-sm">
						<div className="absolute inset-0 bg-gradient-to-br from-secondary/5 via-transparent to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
						<div className="relative flex items-center justify-between mb-3">
							<div className="flex items-center gap-2">
								<div className="p-1.5 rounded-lg bg-secondary/10 group-hover:bg-secondary/20 transition-colors">
									<Calendar className="w-3.5 h-3.5 text-secondary" />
								</div>
								<div>
									<Label className="text-sm font-semibold text-foreground">
										Schedule Publication
									</Label>
									<p className="text-xs text-muted-foreground mt-0.5">Set a future publication date</p>
								</div>
							</div>
							<button
								onClick={() => setIsScheduling(!isScheduling)}
								className={`relative w-14 h-7 rounded-full transition-all duration-300 ${isScheduling 
									? "bg-secondary shadow-lg shadow-secondary/30" 
									: "bg-muted hover:bg-muted/80"
								}`}
							>
								<span
									className={`absolute top-0.5 w-6 h-6 rounded-full bg-background shadow-lg transition-all duration-300 ${isScheduling ? "left-7 translate-x-0" : "left-0.5"
									}`}
								/>
							</button>
						</div>
						{isScheduling && (
							<motion.div
								initial={{ opacity: 0, height: 0 }}
								animate={{ opacity: 1, height: "auto" }}
							>
								<DateTimePicker
									value={scheduleDate}
									onChange={setScheduleDate}
									minDate={new Date()}
									placeholder="Select publication date and time"
								/>
							</motion.div>
						)}
					</div>

					{/* Title */}
					<div className="relative space-y-2 pb-4 border-b border-border/50">
						<Input
							placeholder="Enter your devotional title..."
							value={title}
							onChange={(e) => setTitle(e.target.value)}
							className="border-0 bg-transparent text-2xl md:text-3xl font-serif font-bold text-foreground placeholder:text-muted-foreground/40 focus-visible:ring-0 p-0 h-auto transition-all duration-200"
						/>
						{/* Day of Year Display */}
						<div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-secondary/10 border border-secondary/20">
							<span className="text-xs font-semibold text-secondary uppercase tracking-wide">Day</span>
							<span className="text-xs font-bold text-foreground">
								{dayOfYear.day}-{dayOfYear.totalDays}
							</span>
						</div>
					</div>

					{/* Bible Version Selector */}
					<div className="group relative bg-gradient-to-br from-card to-card/50 rounded-xl border border-border/50 p-4 shadow-sm hover:shadow-md transition-all duration-300">
						<div className="flex items-center gap-2 mb-3">
							<div className="p-1.5 rounded-lg bg-secondary/10 group-hover:bg-secondary/20 transition-colors">
								<BookOpen className="w-3.5 h-3.5 text-secondary" />
							</div>
							<div>
								<Label className="text-sm font-semibold text-foreground block">
									Bible Version
								</Label>
								<p className="text-xs text-muted-foreground mt-0.5">
									Select translation for scripture lookups
								</p>
							</div>
						</div>
						<BibleVersionCombobox
							translations={bibleTranslationsList}
							value={selectedTranslation}
							onValueChange={setSelectedTranslation}
						/>
					</div>

					{/* Reference Scripture */}
					<div className="group relative bg-gradient-to-br from-card to-card/50 rounded-xl border border-border/50 p-4 shadow-sm hover:shadow-md transition-all duration-300">
						<div className="flex items-center gap-2 mb-3">
							<div className="p-1.5 rounded-lg bg-secondary/10 group-hover:bg-secondary/20 transition-colors">
								<BookOpen className="w-3.5 h-3.5 text-secondary" />
							</div>
							<div>
								<Label className="text-sm font-semibold text-foreground block">
									Scripture References
								</Label>
								<p className="text-xs text-muted-foreground mt-0.5">
									Add Bible verses to your devotional
								</p>
							</div>
						</div>
						<div className="relative">
							<Input
								ref={(el) => {
									if (el) {
										(el as any).__scriptureAutocompleteHandler = (e: React.KeyboardEvent<HTMLInputElement>) => {
											// This will be called by ScriptureAutocomplete
										};
									}
								}}
								placeholder="Type a verse reference (e.g., John 3:16)"
								value={scripture}
								onChange={(e) => setScripture(e.target.value)}
								className="h-12 pr-24 border-border/50 focus:border-secondary/50 focus:ring-2 focus:ring-secondary/20 transition-all"
								onKeyDown={(e) => {
									// Let ScriptureAutocomplete handle arrow keys and Enter for autocomplete
									if (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "Escape") {
										// These will be handled by ScriptureAutocomplete
										return;
									}
									// Only handle Enter if autocomplete didn't prevent default
									if (e.key === "Enter" && scripture.trim() && !e.defaultPrevented) {
										e.preventDefault();
										handleLookupScripture();
									}
								}}
							/>
							<ScriptureAutocomplete
								value={scripture}
								onChange={setScripture}
								onSelect={(ref) => {
									setScripture(ref);
								}}
								onKeyDown={(e) => {
									// Only handle Enter if autocomplete didn't prevent default
									if (e.key === "Enter" && scripture.trim() && !e.defaultPrevented) {
										handleLookupScripture();
									}
								}}
							/>
							<Button
								variant="secondary"
								size="sm"
								className="absolute right-2 top-1/2 -translate-y-1/2 z-10 gap-1 shadow-sm hover:shadow-md transition-all"
								onClick={handleLookupScripture}
								disabled={isLookingUpScripture || !scripture.trim()}
							>
								{isLookingUpScripture ? (
									<>
										<Loader2 className="w-4 h-4 animate-spin" />
										Adding...
									</>
								) : (
									<>
										<Plus className="w-4 h-4" />
										Add
									</>
								)}
							</Button>
						</div>

						{/* Display added scripture references */}
						{scriptureReferences.length > 0 && (
							<div className="mt-3 space-y-2">
								{scriptureReferences.map((scriptureData, index) => (
									<motion.div
										key={index}
										initial={{ opacity: 0, height: 0, x: -10 }}
										animate={{ opacity: 1, height: "auto", x: 0 }}
										exit={{ opacity: 0, height: 0, x: -10 }}
										className="relative p-3 bg-gradient-to-r from-secondary/10 via-secondary/5 to-transparent border-l-4 border-secondary rounded-r-lg shadow-sm hover:shadow-md transition-all group/item"
									>
										<Button
											variant="ghost"
											size="icon"
											className="absolute top-2 right-2 h-6 w-6"
											onClick={() => handleRemoveScripture(index)}
										>
											<X className="w-4 h-4" />
										</Button>
										<p className="font-serif text-lg italic text-foreground/90 pr-8">
											"{scriptureData.text}"
										</p>
										<p className="text-sm text-secondary font-medium mt-2">
											— {scriptureData.reference} ({scriptureData.translation_name})
										</p>
									</motion.div>
								))}
							</div>
						)}
					</div>

					{/* Toolbar */}
					<div className="flex flex-wrap items-center gap-1.5 p-2 bg-gradient-to-r from-muted/30 via-muted/20 to-muted/30 rounded-lg border border-border/50 backdrop-blur-sm shadow-sm">
						<Button variant="ghost" size="icon" className="h-9 w-9 hover:bg-secondary/10 hover:text-secondary transition-all">
							<Bold className="w-4 h-4" />
						</Button>
						<Button variant="ghost" size="icon" className="h-9 w-9 hover:bg-secondary/10 hover:text-secondary transition-all">
							<Italic className="w-4 h-4" />
						</Button>
						<Button variant="ghost" size="icon" className="h-9 w-9 hover:bg-secondary/10 hover:text-secondary transition-all">
							<List className="w-4 h-4" />
						</Button>
						<Button variant="ghost" size="icon" className="h-9 w-9 hover:bg-secondary/10 hover:text-secondary transition-all">
							<Quote className="w-4 h-4" />
						</Button>
						<div className="w-px h-6 bg-border/50 mx-1" />
						<DropdownMenu>
							<DropdownMenuTrigger asChild>
								<Button
									variant="ghost"
									size="icon"
									className="h-9 w-9"
									disabled={isUploadingImage}
								>
									{isUploadingImage ? (
										<Loader2 className="w-4 h-4 animate-spin" />
									) : (
										<Image className="w-4 h-4" />
									)}
								</Button>
							</DropdownMenuTrigger>
							<DropdownMenuContent>
								<DropdownMenuItem onClick={handleImageClick}>
									<Upload className="w-4 h-4 mr-2" />
									Upload from Computer
								</DropdownMenuItem>
								<DropdownMenuItem onClick={() => setIsImageSearchOpen(true)}>
									<Sparkles className="w-4 h-4 mr-2" />
									Search Stock Photos
								</DropdownMenuItem>
							</DropdownMenuContent>
						</DropdownMenu>
						<input
							ref={imageInputRef}
							type="file"
							accept="image/*"
							onChange={handleImageChange}
							className="hidden"
						/>
						<Button variant="ghost" size="icon" className="h-9 w-9">
							<Mic className="w-4 h-4" />
						</Button>
						<Button variant="ghost" size="icon" className="h-9 w-9">
							<Video className="w-4 h-4" />
						</Button>
						<div className="flex-1" />
						<Button
							variant="ghost"
							size="sm"
							className="gap-2 text-secondary"
						>
							<Sparkles className="w-4 h-4" />
							<span className="hidden sm:inline">AI Assist</span>
						</Button>
					</div>

					{/* Cover Image Preview */}
					{coverImage && (
						<motion.div
							initial={{ opacity: 0, y: -10 }}
							animate={{ opacity: 1, y: 0 }}
							className="relative rounded-2xl overflow-hidden border border-border/50 shadow-lg group/image"
						>
							<img
								src={coverImage}
								alt="Cover"
								className="w-full h-64 object-cover transition-transform duration-300 group-hover/image:scale-105"
							/>
							<Button
								variant="destructive"
								size="icon"
								className="absolute top-4 right-4 shadow-lg hover:shadow-xl transition-all opacity-90 hover:opacity-100"
								onClick={handleRemoveImage}
							>
								<X className="w-4 h-4" />
							</Button>
							<div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-4">
								{imageAttribution ? (
									<div className="text-white space-y-1">
										<p className="text-sm font-medium flex items-center gap-2">
											<Sparkles className="w-4 h-4" />
											Stock Photo Selected
										</p>
										<p className="text-xs opacity-90">
											Photo by{" "}
											<a
												href={imageAttribution.url}
												target="_blank"
												rel="noopener noreferrer"
												className="underline hover:text-secondary"
											>
												{imageAttribution.photographer}
											</a>
											{" "}from Pexels
										</p>
									</div>
								) : (
									<p className="text-white text-sm font-medium flex items-center gap-2">
										<Upload className="w-4 h-4" />
										Cover Image Uploaded
									</p>
								)}
							</div>
						</motion.div>
					)}

					{/* Content */}
					<div className="relative">
						<div className="absolute -inset-0.5 bg-gradient-to-r from-secondary/20 via-transparent to-secondary/20 rounded-xl blur-sm opacity-0 hover:opacity-100 transition-opacity duration-300" />
						<div className="relative bg-card/50 rounded-xl border border-border/50 p-4 shadow-sm">
							<Textarea
								placeholder="Begin writing your devotional message... Let the Spirit guide your words."
								value={content}
								onChange={(e) => setContent(e.target.value)}
								className="min-h-[250px] border-0 bg-transparent text-base text-foreground placeholder:text-muted-foreground/40 focus-visible:ring-0 p-0 resize-none leading-relaxed font-serif"
							/>
						</div>
					</div>

					{/* Reflection Section */}
					<div className="group relative bg-gradient-to-br from-card to-card/50 rounded-xl border border-border/50 p-4 shadow-sm hover:shadow-md transition-all duration-300">
						<div className="flex items-center gap-2 mb-3">
							<div className="p-1.5 rounded-lg bg-secondary/10 group-hover:bg-secondary/20 transition-colors">
								<Sparkles className="w-3.5 h-3.5 text-secondary" />
							</div>
							<div>
								<Label className="text-sm font-semibold text-foreground block">
									Reflection
								</Label>
								<p className="text-xs text-muted-foreground mt-0.5">
									Help readers apply this message to their lives
								</p>
							</div>
						</div>
						<Textarea
							placeholder="Share reflection questions or thoughts to help readers apply this message..."
							value={reflection}
							onChange={(e) => setReflection(e.target.value)}
							className="min-h-[120px] border border-border/50 bg-background/50 rounded-lg text-sm text-foreground placeholder:text-muted-foreground/40 focus-visible:ring-2 focus-visible:ring-secondary/20 focus-visible:border-secondary/50 p-3 resize-none leading-relaxed transition-all"
						/>
					</div>

					{/* Prayer Section */}
					<div className="group relative bg-gradient-to-br from-card to-card/50 rounded-xl border border-border/50 p-4 shadow-sm hover:shadow-md transition-all duration-300">
						<div className="flex items-center gap-2 mb-3">
							<div className="p-1.5 rounded-lg bg-secondary/10 group-hover:bg-secondary/20 transition-colors">
								<Sparkles className="w-3.5 h-3.5 text-secondary" />
							</div>
							<div>
								<Label className="text-sm font-semibold text-foreground block">
									Prayer
								</Label>
								<p className="text-xs text-muted-foreground mt-0.5">
									Guide readers to connect with God
								</p>
							</div>
						</div>
						<Textarea
							placeholder="Write a prayer that closes the devotional... Guide readers to connect with God."
							value={prayer}
							onChange={(e) => setPrayer(e.target.value)}
							className="min-h-[120px] border border-border/50 bg-background/50 rounded-lg text-sm text-foreground placeholder:text-muted-foreground/40 focus-visible:ring-2 focus-visible:ring-secondary/20 focus-visible:border-secondary/50 p-3 resize-none leading-relaxed font-serif italic transition-all"
						/>
					</div>

					{/* Other Bible References */}
					<div className="group relative bg-gradient-to-br from-card to-card/50 rounded-xl border border-border/50 p-4 shadow-sm hover:shadow-md transition-all duration-300">
						<div className="flex items-center gap-2 mb-3">
							<div className="p-1.5 rounded-lg bg-secondary/10 group-hover:bg-secondary/20 transition-colors">
								<BookOpen className="w-3.5 h-3.5 text-secondary" />
							</div>
							<div>
								<Label className="text-sm font-semibold text-foreground block">
									Other Bible References
								</Label>
								<p className="text-xs text-muted-foreground mt-0.5">
									Additional verses related to this devotional
								</p>
							</div>
						</div>
						<Textarea
							placeholder="Enter additional Bible references (e.g., John 3:16, Romans 8:28, Philippians 4:13)..."
							value={otherBibleReferences}
							onChange={(e) => setOtherBibleReferences(e.target.value)}
							className="min-h-[80px] border border-border/50 bg-background/50 rounded-lg text-sm text-foreground placeholder:text-muted-foreground/40 focus-visible:ring-2 focus-visible:ring-secondary/20 focus-visible:border-secondary/50 p-3 resize-none leading-relaxed transition-all"
						/>
					</div>

					{/* Categories */}
					<div className="group relative bg-gradient-to-br from-card to-card/50 rounded-xl border border-border/50 p-4 shadow-sm hover:shadow-md transition-all duration-300">
						<div className="flex items-center gap-2 mb-3">
							<div className="p-1.5 rounded-lg bg-secondary/10 group-hover:bg-secondary/20 transition-colors">
								<Tag className="w-3.5 h-3.5 text-secondary" />
							</div>
							<div>
								<Label className="text-sm font-semibold text-foreground block">
									Categories
								</Label>
								<p className="text-xs text-muted-foreground mt-0.5">
									Tag your devotional for better discoverability
								</p>
							</div>
						</div>
						<div className="flex flex-wrap gap-2">
							{categories.map((category) => (
								<button
									key={category}
									onClick={() => toggleCategory(category)}
									className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
										selectedCategories.includes(category)
											? "bg-gradient-to-r from-secondary to-secondary/80 text-secondary-foreground shadow-md shadow-secondary/30 scale-105"
											: "bg-muted/50 text-muted-foreground hover:bg-muted hover:scale-105 border border-border/50"
									}`}
								>
									{category}
								</button>
							))}
						</div>
					</div>
				</motion.div>
			</div>

			{/* Image Search Dialog */}
			<ImageSearchDialog
				open={isImageSearchOpen}
				onClose={() => setIsImageSearchOpen(false)}
				onSelectImage={handleSelectStockPhoto}
			/>

			{/* Preview Dialog */}
			<DevotionalPreview
				open={isPreviewOpen}
				onClose={() => setIsPreviewOpen(false)}
				devotionalData={{
					title,
					content,
					scripture: scriptureReferences.length > 0 ? scriptureReferences[0].text : "",
					scriptureReference: scriptureReferences.length > 0 ? scriptureReferences[0].reference : "",
					scriptureTranslation: scriptureReferences.length > 0 ? scriptureReferences[0].translation_name : "",
					prayer,
					reflection,
					coverImage,
					categories: selectedCategories,
					scheduleDate,
					imageAttribution,
				}}
				authorName="You"
			/>
		</div>
	);
};

export default Compose;
