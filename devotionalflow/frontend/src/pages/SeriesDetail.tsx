import { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
	BookOpen,
	User,
	ChevronLeft,
	Play,
	CheckCircle2,
	Circle,
	Calendar,
} from "lucide-react";
import { MainNavigation } from "@/components/navigation/MainNavigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";

interface Series {
	id: string;
	name: string;
	slug: string;
	description?: string;
	cover_image_url?: string;
	author_name: string;
	author_id: string;
	total_parts: number;
	start_date?: string;
	devotionals_count?: number;
}

interface Devotional {
	id: string;
	title: string;
	slug: string;
	part_number: number;
	status: string;
	published_at?: string;
	scheduled_at?: string;
	reading_time_minutes?: number;
	excerpt?: string;
	is_read?: boolean;
	reading_progress?: number;
}

/**
 * SeriesDetail - Display series information and list of devotionals
 * Shows hero section, progress tracker, and devotional list with day numbers
 */
export default function SeriesDetail() {
	const { id } = useParams<{ id: string }>();
	const navigate = useNavigate();
	const { toast } = useToast();
	const { user } = useAuth();

	const [series, setSeries] = useState<Series | null>(null);
	const [devotionals, setDevotionals] = useState<Devotional[]>([]);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		if (id) {
			loadSeriesData();
		}
	}, [id]);

	const loadSeriesData = async () => {
		setLoading(true);
		try {
			// Load series details and devotionals in parallel
			const [seriesData, devotionalsData] = await Promise.all([
				apiClient.getSeries(id!),
				apiClient.getSeriesDevotionals(id!),
			]);

			setSeries(seriesData);
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

	const publishedDevotionals = devotionals.filter((d) => d.status === "published");
	// Find next unread devotional (first one that is not read, or first one if all are read)
	const nextUnreadDevotional = user
		? publishedDevotionals.find((d) => !d.is_read) || publishedDevotionals[0]
		: publishedDevotionals[0];

	if (loading) {
		return (
			<div className="min-h-screen bg-background">
				<MainNavigation />
				<div className="container mx-auto px-4 py-12">
					<SeriesDetailSkeleton />
				</div>
			</div>
		);
	}

	if (!series) {
		return (
			<div className="min-h-screen bg-background">
				<MainNavigation />
				<div className="container mx-auto px-4 py-12 text-center">
					<h2 className="text-2xl font-bold text-foreground mb-4">Series not found</h2>
					<Button onClick={() => navigate("/series")}>Back to Series</Button>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-background">
			<MainNavigation />

			{/* Back Button */}
			<div className="container mx-auto px-4 pt-6">
				<Button
					variant="ghost"
					onClick={() => navigate("/series")}
					className="gap-2"
				>
					<ChevronLeft className="w-4 h-4" />
					Back to Series
				</Button>
			</div>

			{/* Hero Section */}
			<motion.div
				initial={{ opacity: 0, y: 20 }}
				animate={{ opacity: 1, y: 0 }}
				transition={{ duration: 0.6 }}
				className="container mx-auto px-4 py-8 md:py-12"
			>
				<div className="max-w-4xl mx-auto">
					<div className="grid md:grid-cols-[300px_1fr] gap-8 items-start">
						{/* Cover Image */}
						{series.cover_image_url ? (
							<div className="rounded-2xl overflow-hidden shadow-lg">
								<img
									src={series.cover_image_url}
									alt={series.name}
									className="w-full aspect-[3/4] object-cover"
								/>
							</div>
						) : (
							<div className="rounded-2xl bg-gradient-to-br from-secondary/20 via-accent/10 to-primary/20 aspect-[3/4] flex items-center justify-center shadow-lg">
								<BookOpen className="w-20 h-20 text-secondary/40" />
							</div>
						)}

						{/* Series Info */}
						<div>
							<h1 className="font-serif text-3xl md:text-4xl lg:text-5xl font-bold text-foreground mb-4">
								{series.name}
							</h1>

							{/* Author */}
							<div className="flex items-center gap-2 text-muted-foreground mb-4">
								<User className="w-4 h-4" />
								<span className="text-sm font-medium">{series.author_name}</span>
							</div>

							{/* Stats */}
							<div className="flex items-center gap-4 mb-6">
								<Badge variant="secondary" className="gap-2">
									<BookOpen className="w-4 h-4" />
									{series.total_parts} {series.total_parts === 1 ? "Part" : "Parts"}
								</Badge>

								{series.start_date && (
									<Badge variant="outline" className="gap-2">
										<Calendar className="w-4 h-4" />
										{new Date(series.start_date).toLocaleDateString("en-US", {
											month: "short",
											day: "numeric",
											year: "numeric",
										})}
									</Badge>
								)}
							</div>

							{/* Description */}
							{series.description && (
								<p className="text-muted-foreground leading-relaxed mb-6">
									{series.description}
								</p>
							)}

							{/* Continue Reading Button */}
							{nextUnreadDevotional && (
								<Button
									onClick={() => navigate(`/devotional/${nextUnreadDevotional.id}`)}
									size="lg"
									className="gap-2"
								>
									<Play className="w-5 h-5" />
									Continue Reading
								</Button>
							)}
						</div>
					</div>
				</div>
			</motion.div>

			{/* Devotionals List */}
			<div className="container mx-auto px-4 py-8 md:py-12">
				<div className="max-w-4xl mx-auto">
					<h2 className="font-serif text-2xl md:text-3xl font-bold text-foreground mb-6">
						Devotionals in this Series
					</h2>

					{devotionals.length === 0 ? (
						<Card>
							<CardContent className="py-12 text-center">
								<p className="text-muted-foreground">
									No devotionals in this series yet.
								</p>
							</CardContent>
						</Card>
					) : (
						<div className="space-y-4">
							{devotionals.map((devotional, index) => (
								<DevotionalListItem
									key={devotional.id}
									devotional={devotional}
									index={index}
									isPublished={devotional.status === "published"}
								/>
							))}
						</div>
					)}
				</div>
			</div>
		</div>
	);
}

/**
 * DevotionalListItem - Single devotional in series list
 */
function DevotionalListItem({
	devotional,
	index,
	isPublished,
}: {
	devotional: Devotional;
	index: number;
	isPublished: boolean;
}) {
	const navigate = useNavigate();
	const isRead = devotional.is_read || false;

	return (
		<motion.div
			initial={{ opacity: 0, x: -20 }}
			animate={{ opacity: 1, x: 0 }}
			transition={{ duration: 0.3, delay: index * 0.05 }}
		>
			<Card
				className={`hover:shadow-md transition-all cursor-pointer ${
					!isPublished ? "opacity-60" : ""
				}`}
				onClick={() => isPublished && navigate(`/devotional/${devotional.id}`)}
			>
				<CardContent className="p-6">
					<div className="flex items-start gap-4">
						{/* Day Number */}
						<div className="flex-shrink-0">
							<div className="w-16 h-16 rounded-full bg-secondary/10 flex items-center justify-center">
								<span className="font-serif text-xl font-bold text-secondary">
									{devotional.part_number}
								</span>
							</div>
						</div>

						{/* Content */}
						<div className="flex-1 min-w-0">
							<div className="flex items-start justify-between gap-4 mb-2">
								<h3 className="font-serif text-xl font-bold text-foreground line-clamp-2">
									{devotional.title}
								</h3>

								{isRead && (
									<CheckCircle2 className="w-6 h-6 text-secondary flex-shrink-0" />
								)}
							</div>

							{devotional.excerpt && (
								<p className="text-muted-foreground text-sm line-clamp-2 mb-3">
									{devotional.excerpt}
								</p>
							)}

							<div className="flex items-center gap-4 text-xs text-muted-foreground">
								{devotional.published_at && (
									<span>
										Published{" "}
										{new Date(devotional.published_at).toLocaleDateString("en-US", {
											month: "short",
											day: "numeric",
										})}
									</span>
								)}

								{devotional.reading_time_minutes && (
									<span>{devotional.reading_time_minutes} min read</span>
								)}

								{!isPublished && (
									<Badge variant="outline" className="text-xs">
										{devotional.status}
									</Badge>
								)}
							</div>
						</div>

						{/* Status Icon */}
						<div className="flex-shrink-0">
							{isRead ? (
								<CheckCircle2 className="w-5 h-5 text-secondary" />
							) : (
								<Circle className="w-5 h-5 text-muted-foreground" />
							)}
						</div>
					</div>
				</CardContent>
			</Card>
		</motion.div>
	);
}

/**
 * SeriesDetailSkeleton - Loading state for series detail
 */
function SeriesDetailSkeleton() {
	return (
		<div className="max-w-4xl mx-auto">
			<div className="grid md:grid-cols-[300px_1fr] gap-8 animate-pulse">
				{/* Cover Image Skeleton */}
				<div className="rounded-2xl bg-muted aspect-[3/4]" />

				{/* Info Skeleton */}
				<div>
					<div className="h-12 w-3/4 bg-muted rounded mb-4" />
					<div className="h-6 w-1/2 bg-muted rounded mb-6" />
					<div className="h-4 w-full bg-muted rounded mb-2" />
					<div className="h-4 w-full bg-muted rounded mb-2" />
					<div className="h-4 w-3/4 bg-muted rounded mb-6" />
					<div className="h-12 w-40 bg-muted rounded" />
				</div>
			</div>
		</div>
	);
}
