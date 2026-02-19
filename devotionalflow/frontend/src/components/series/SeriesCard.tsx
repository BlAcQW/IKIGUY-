import { motion } from "framer-motion";
import { BookOpen, User } from "lucide-react";
import { Link } from "react-router-dom";

interface SeriesCardProps {
	id: string;
	name: string;
	slug: string;
	description?: string;
	cover_image_url?: string;
	author_name: string;
	total_parts: number;
	devotionals_count?: number;
	index?: number; // For staggered animations
}

/**
 * SeriesCard - Display card for a devotional series
 * Shows series cover, title, description, author, and devotional count
 * Optimized for browse pages with hover effects and animations
 */
export function SeriesCard({
	id,
	name,
	slug,
	description,
	cover_image_url,
	author_name,
	total_parts,
	devotionals_count,
	index = 0,
}: SeriesCardProps) {
	const count = devotionals_count ?? total_parts;

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			transition={{ duration: 0.4, delay: index * 0.05 }}
		>
			<Link to={`/series/${id}`}>
				<div className="bg-card rounded-3xl border border-border overflow-hidden hover:shadow-elevated hover:scale-[1.02] transition-all duration-300 group h-full">
					{/* Cover Image */}
					{cover_image_url ? (
						<div className="relative h-48 md:h-56 overflow-hidden">
							<img
								src={cover_image_url}
								alt={name}
								className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
							/>
							{/* Gradient Overlay */}
							<div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />

							{/* Devotional Count Badge */}
							<div className="absolute bottom-4 right-4 bg-white/95 dark:bg-black/95 backdrop-blur-sm px-4 py-2 rounded-full">
								<div className="flex items-center gap-2">
									<BookOpen className="w-4 h-4 text-secondary" />
									<span className="text-sm font-semibold text-foreground">
										{count} {count === 1 ? "Devotional" : "Devotionals"}
									</span>
								</div>
							</div>
						</div>
					) : (
						<div className="relative h-48 md:h-56 bg-gradient-to-br from-secondary/20 via-accent/10 to-primary/20 flex items-center justify-center">
							<BookOpen className="w-16 h-16 text-secondary/40" />

							{/* Devotional Count Badge */}
							<div className="absolute bottom-4 right-4 bg-white/95 dark:bg-black/95 backdrop-blur-sm px-4 py-2 rounded-full">
								<div className="flex items-center gap-2">
									<BookOpen className="w-4 h-4 text-secondary" />
									<span className="text-sm font-semibold text-foreground">
										{count} {count === 1 ? "Devotional" : "Devotionals"}
									</span>
								</div>
							</div>
						</div>
					)}

					{/* Content */}
					<div className="p-6">
						{/* Title */}
						<h3 className="font-serif text-2xl font-bold text-foreground mb-3 line-clamp-2 group-hover:text-secondary transition-colors">
							{name}
						</h3>

						{/* Description */}
						{description && (
							<p className="text-muted-foreground text-sm leading-relaxed mb-4 line-clamp-3">
								{description}
							</p>
						)}

						{/* Author */}
						<div className="flex items-center gap-2 text-muted-foreground">
							<User className="w-4 h-4" />
							<span className="text-sm font-medium">{author_name}</span>
						</div>
					</div>
				</div>
			</Link>
		</motion.div>
	);
}

/**
 * SeriesCardGrid - Grid layout for series cards
 * Responsive: 1 column (mobile), 2 columns (tablet), 3 columns (desktop)
 */
export function SeriesCardGrid({ children }: { children: React.ReactNode }) {
	return (
		<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8">
			{children}
		</div>
	);
}
