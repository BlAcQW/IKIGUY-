import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Search, BookOpen, Sparkles } from "lucide-react";
import { MainNavigation } from "@/components/navigation/MainNavigation";
import { Input } from "@/components/ui/input";
import { SeriesCard, SeriesCardGrid } from "@/components/series/SeriesCard";
import { SeriesGridSkeleton } from "@/components/loading/DevotionalCardSkeleton";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface Series {
	id: string;
	name: string;
	slug: string;
	description?: string;
	cover_image_url?: string;
	author_name: string;
	author_id: string;
	total_parts: number;
	devotionals_count?: number;
	created_at: string;
	updated_at: string;
}

/**
 * Series - Public page to browse all devotional series
 * Displays series in a responsive grid with search functionality
 */
export default function Series() {
	const { toast } = useToast();
	const [series, setSeries] = useState<Series[]>([]);
	const [loading, setLoading] = useState(true);
	const [searchQuery, setSearchQuery] = useState("");

	useEffect(() => {
		loadSeries();
	}, []);

	const loadSeries = async () => {
		setLoading(true);
		try {
			const response = await apiClient.listSeries();
			setSeries(response);
		} catch (error) {
			console.error("Failed to load series:", error);
			toast({
				title: "Error",
				description: "Failed to load devotional series",
				variant: "destructive",
			});
		} finally {
			setLoading(false);
		}
	};

	const filteredSeries = series.filter(
		(s) =>
			s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			s.author_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			s.description?.toLowerCase().includes(searchQuery.toLowerCase())
	);

	return (
		<div className="min-h-screen bg-background">
			<MainNavigation />

			{/* Header Section */}
			<motion.div
				initial={{ opacity: 0, y: 20 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ duration: 0.6 }}
				className="border-b border-border/50 bg-gradient-to-b from-secondary/5 to-transparent"
			>
				<div className="container mx-auto px-4 py-16 md:py-24">
					<div className="max-w-3xl mx-auto text-center">
						<div className="inline-flex items-center gap-2 bg-secondary/10 text-secondary px-4 py-2 rounded-full mb-6">
							<Sparkles className="w-4 h-4" />
							<span className="text-sm font-medium">Devotional Collections</span>
						</div>

						<h1 className="font-serif text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-6">
							Devotional Series
						</h1>

						<p className="text-lg md:text-xl text-muted-foreground leading-relaxed mb-8">
							Explore curated collections of devotionals designed to guide you through
							multi-day spiritual journeys.
						</p>

						{/* Search Bar */}
						<div className="relative max-w-xl mx-auto">
							<Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
							<Input
								type="text"
								placeholder="Search series by name, author, or description..."
								value={searchQuery}
								onChange={(e) => setSearchQuery(e.target.value)}
								className="pl-12 h-12 rounded-full border-border/50 bg-card shadow-sm"
							/>
						</div>
					</div>
				</div>
			</motion.div>

			{/* Series Grid */}
			<div className="container mx-auto px-4 py-12 md:py-16">
				{loading ? (
					<SeriesGridSkeleton count={6} />
				) : filteredSeries.length === 0 ? (
					<EmptyState
						hasSearch={searchQuery.length > 0}
						searchQuery={searchQuery}
						onClearSearch={() => setSearchQuery("")}
					/>
				) : (
					<>
						{/* Results Count */}
						<div className="mb-6 text-center">
							<p className="text-muted-foreground">
								{filteredSeries.length === series.length ? (
									<>
										<span className="font-semibold text-foreground">
											{filteredSeries.length}
										</span>{" "}
										{filteredSeries.length === 1 ? "series" : "series"} available
									</>
								) : (
									<>
										<span className="font-semibold text-foreground">
											{filteredSeries.length}
										</span>{" "}
										of {series.length} series match your search
									</>
								)}
							</p>
						</div>

						{/* Series Cards */}
						<SeriesCardGrid>
							{filteredSeries.map((s, index) => (
								<SeriesCard
									key={s.id}
									id={s.id}
									name={s.name}
									slug={s.slug}
									description={s.description}
									cover_image_url={s.cover_image_url}
									author_name={s.author_name}
									total_parts={s.total_parts}
									devotionals_count={s.devotionals_count}
									index={index}
								/>
							))}
						</SeriesCardGrid>
					</>
				)}
			</div>
		</div>
	);
}

/**
 * EmptyState - Display when no series are available
 */
function EmptyState({
	hasSearch,
	searchQuery,
	onClearSearch,
}: {
	hasSearch: boolean;
	searchQuery: string;
	onClearSearch: () => void;
}) {
	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			transition={{ duration: 0.4 }}
			className="text-center py-20"
		>
			<div className="max-w-md mx-auto">
				<div className="w-20 h-20 mx-auto mb-6 rounded-full bg-secondary/10 flex items-center justify-center">
					<BookOpen className="w-10 h-10 text-secondary" />
				</div>

				{hasSearch ? (
					<>
						<h3 className="font-serif text-2xl font-bold text-foreground mb-3">
							No series found
						</h3>
						<p className="text-muted-foreground mb-6">
							No series match <span className="font-semibold">"{searchQuery}"</span>.
							Try a different search term.
						</p>
						<button
							onClick={onClearSearch}
							className="text-secondary hover:text-secondary/80 font-medium transition-colors"
						>
							Clear search
						</button>
					</>
				) : (
					<>
						<h3 className="font-serif text-2xl font-bold text-foreground mb-3">
							No series available yet
						</h3>
						<p className="text-muted-foreground">
							Check back soon for new devotional series!
						</p>
					</>
				)}
			</div>
		</motion.div>
	);
}
