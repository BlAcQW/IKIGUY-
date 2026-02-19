import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
	Search,
	X,
	Loader2,
	Upload,
	Image as ImageIcon,
	ExternalLink,
	Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface PexelsPhoto {
	id: number;
	width: number;
	height: number;
	url: string;
	photographer: string;
	photographer_url: string;
	avg_color: string;
	alt: string;
	src: {
		original: string;
		large2x: string;
		large: string;
		medium: string;
		small: string;
		portrait: string;
		landscape: string;
		tiny: string;
	};
}

interface ImageSearchDialogProps {
	open: boolean;
	onClose: () => void;
	onSelectImage: (imageUrl: string, attribution?: { photographer: string; url: string }) => void;
}

export function ImageSearchDialog({ open, onClose, onSelectImage }: ImageSearchDialogProps) {
	const { toast } = useToast();
	const [searchQuery, setSearchQuery] = useState("");
	const [isSearching, setIsSearching] = useState(false);
	const [photos, setPhotos] = useState<PexelsPhoto[]>([]);
	const [selectedPhoto, setSelectedPhoto] = useState<PexelsPhoto | null>(null);
	const [showCurated, setShowCurated] = useState(true);

	// Load curated photos on mount
	useEffect(() => {
		if (open && showCurated) {
			loadCuratedPhotos();
		}
	}, [open]);

	const loadCuratedPhotos = async () => {
		setIsSearching(true);
		try {
			const response = await apiClient.client.get("/media/pexels/curated", {
				params: { per_page: 20, page: 1 },
			});
			setPhotos(response.data.photos || []);
		} catch (error: any) {
			console.error("Failed to load curated photos:", error);
			toast({
				title: "Failed to load photos",
				description: error.response?.data?.detail || "Could not load curated photos",
				variant: "destructive",
			});
		} finally {
			setIsSearching(false);
		}
	};

	const handleSearch = async () => {
		if (!searchQuery.trim()) {
			toast({
				title: "Enter search keywords",
				description: "Please enter keywords like 'faith', 'prayer', or 'nature'",
				variant: "destructive",
			});
			return;
		}

		setIsSearching(true);
		setShowCurated(false);
		try {
			const response = await apiClient.client.get("/media/pexels/search", {
				params: {
					query: searchQuery,
					per_page: 20,
					page: 1,
					orientation: "landscape",
				},
			});
			setPhotos(response.data.photos || []);

			if (response.data.photos?.length === 0) {
				toast({
					title: "No results found",
					description: `No photos found for "${searchQuery}". Try different keywords.`,
				});
			}
		} catch (error: any) {
			console.error("Search failed:", error);
			toast({
				title: "Search failed",
				description: error.response?.data?.detail || "Could not search photos",
				variant: "destructive",
			});
		} finally {
			setIsSearching(false);
		}
	};

	const handleSelectPhoto = (photo: PexelsPhoto) => {
		setSelectedPhoto(photo);
	};

	const handleUsePhoto = () => {
		if (!selectedPhoto) return;

		// Use the large image URL
		onSelectImage(selectedPhoto.src.large, {
			photographer: selectedPhoto.photographer,
			url: selectedPhoto.photographer_url,
		});

		toast({
			title: "Image selected",
			description: `Photo by ${selectedPhoto.photographer} from Pexels`,
		});

		onClose();
	};

	const handleKeyPress = (e: React.KeyboardEvent) => {
		if (e.key === "Enter" && searchQuery.trim()) {
			handleSearch();
		}
	};

	return (
		<Dialog open={open} onOpenChange={onClose}>
			<DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
				<DialogHeader>
					<DialogTitle className="flex items-center gap-2">
						<Sparkles className="w-5 h-5 text-secondary" />
						Stock Photo Search
					</DialogTitle>
				</DialogHeader>

				<Tabs defaultValue="search" className="flex-1 flex flex-col min-h-0">
					<TabsList className="grid w-full grid-cols-2">
						<TabsTrigger value="search">Search</TabsTrigger>
						<TabsTrigger value="curated" onClick={loadCuratedPhotos}>
							Curated
						</TabsTrigger>
					</TabsList>

					<TabsContent value="search" className="flex-1 flex flex-col min-h-0 space-y-4">
						{/* Search Input */}
						<div className="relative">
							<Input
								placeholder="Search for faith, prayer, nature, worship..."
								value={searchQuery}
								onChange={(e) => setSearchQuery(e.target.value)}
								onKeyPress={handleKeyPress}
								className="pr-24"
							/>
							<Button
								variant="secondary"
								size="sm"
								className="absolute right-2 top-1/2 -translate-y-1/2"
								onClick={handleSearch}
								disabled={isSearching || !searchQuery.trim()}
							>
								{isSearching ? (
									<>
										<Loader2 className="w-4 h-4 mr-2 animate-spin" />
										Searching...
									</>
								) : (
									<>
										<Search className="w-4 h-4 mr-2" />
										Search
									</>
								)}
							</Button>
						</div>

						{/* Photo Grid */}
						<div className="flex-1 overflow-y-auto">
							{isSearching ? (
								<div className="flex items-center justify-center h-64">
									<Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
								</div>
							) : photos.length > 0 ? (
								<div className="grid grid-cols-2 md:grid-cols-3 gap-4">
									{photos.map((photo) => (
										<motion.div
											key={photo.id}
											initial={{ opacity: 0, scale: 0.9 }}
											animate={{ opacity: 1, scale: 1 }}
											className={`relative aspect-video rounded-lg overflow-hidden cursor-pointer border-2 transition-all ${
												selectedPhoto?.id === photo.id
													? "border-secondary ring-2 ring-secondary/20"
													: "border-transparent hover:border-muted-foreground/20"
											}`}
											onClick={() => handleSelectPhoto(photo)}
										>
											<img
												src={photo.src.medium}
												alt={photo.alt}
												className="w-full h-full object-cover"
												loading="lazy"
											/>
											{selectedPhoto?.id === photo.id && (
												<div className="absolute inset-0 bg-secondary/20 flex items-center justify-center">
													<div className="bg-secondary text-secondary-foreground rounded-full p-2">
														<ImageIcon className="w-6 h-6" />
													</div>
												</div>
											)}
											<div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
												<p className="text-white text-xs truncate">
													Photo by {photo.photographer}
												</p>
											</div>
										</motion.div>
									))}
								</div>
							) : (
								<div className="flex flex-col items-center justify-center h-64 text-center">
									<Search className="w-12 h-12 text-muted-foreground mb-4" />
									<p className="text-muted-foreground">
										Search for beautiful stock photos to use as your devotional cover
									</p>
									<p className="text-sm text-muted-foreground mt-2">
										Try: "faith", "prayer", "nature", "worship", "bible"
									</p>
								</div>
							)}
						</div>
					</TabsContent>

					<TabsContent value="curated" className="flex-1 flex flex-col min-h-0">
						<div className="flex-1 overflow-y-auto">
							{isSearching ? (
								<div className="flex items-center justify-center h-64">
									<Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
								</div>
							) : photos.length > 0 ? (
								<div className="grid grid-cols-2 md:grid-cols-3 gap-4">
									{photos.map((photo) => (
										<motion.div
											key={photo.id}
											initial={{ opacity: 0, scale: 0.9 }}
											animate={{ opacity: 1, scale: 1 }}
											className={`relative aspect-video rounded-lg overflow-hidden cursor-pointer border-2 transition-all ${
												selectedPhoto?.id === photo.id
													? "border-secondary ring-2 ring-secondary/20"
													: "border-transparent hover:border-muted-foreground/20"
											}`}
											onClick={() => handleSelectPhoto(photo)}
										>
											<img
												src={photo.src.medium}
												alt={photo.alt}
												className="w-full h-full object-cover"
												loading="lazy"
											/>
											{selectedPhoto?.id === photo.id && (
												<div className="absolute inset-0 bg-secondary/20 flex items-center justify-center">
													<div className="bg-secondary text-secondary-foreground rounded-full p-2">
														<ImageIcon className="w-6 h-6" />
													</div>
												</div>
											)}
											<div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
												<p className="text-white text-xs truncate">
													Photo by {photo.photographer}
												</p>
											</div>
										</motion.div>
									))}
								</div>
							) : (
								<div className="flex flex-col items-center justify-center h-64 text-center">
									<Sparkles className="w-12 h-12 text-muted-foreground mb-4" />
									<p className="text-muted-foreground">
										Hand-picked high-quality photos from Pexels
									</p>
								</div>
							)}
						</div>
					</TabsContent>
				</Tabs>

				{/* Footer with Selected Photo Info */}
				<AnimatePresence>
					{selectedPhoto && (
						<motion.div
							initial={{ opacity: 0, y: 20 }}
							animate={{ opacity: 1, y: 0 }}
							exit={{ opacity: 0, y: 20 }}
							className="border-t pt-4 space-y-3"
						>
							<div className="flex items-center gap-3">
								<div className="flex-1">
									<p className="text-sm font-medium">Selected Photo</p>
									<p className="text-xs text-muted-foreground">
										Photo by{" "}
										<a
											href={selectedPhoto.photographer_url}
											target="_blank"
											rel="noopener noreferrer"
											className="text-secondary hover:underline inline-flex items-center gap-1"
										>
											{selectedPhoto.photographer}
											<ExternalLink className="w-3 h-3" />
										</a>
									</p>
									<p className="text-xs text-muted-foreground mt-1">
										From{" "}
										<a
											href="https://www.pexels.com"
											target="_blank"
											rel="noopener noreferrer"
											className="text-secondary hover:underline"
										>
											Pexels
										</a>
									</p>
								</div>
								<Button onClick={handleUsePhoto} variant="hero">
									<Upload className="w-4 h-4 mr-2" />
									Use This Photo
								</Button>
							</div>
						</motion.div>
					)}
				</AnimatePresence>
			</DialogContent>
		</Dialog>
	);
}
