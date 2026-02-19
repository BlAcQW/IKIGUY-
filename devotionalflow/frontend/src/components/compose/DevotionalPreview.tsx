import { motion } from "framer-motion";
import {
	X,
	Calendar,
	BookOpen,
	Tag,
	Clock,
	Sparkles,
	ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { format } from "date-fns";
import { getImageUrl } from "@/lib/image-utils";

interface PreviewProps {
	open: boolean;
	onClose: () => void;
	devotionalData: {
		title: string;
		content: string;
		scripture: string;
		scriptureReference: string;
		scriptureTranslation: string;
		prayer: string;
		reflection: string;
		coverImage: string | null;
		categories: string[];
		scheduleDate: Date | null;
		imageAttribution?: {
			photographer: string;
			url: string;
		} | null;
	};
	authorName?: string;
}

export function DevotionalPreview({
	open,
	onClose,
	devotionalData,
	authorName = "Your Name",
}: PreviewProps) {
	const {
		title,
		content,
		scripture,
		scriptureReference,
		scriptureTranslation,
		prayer,
		reflection,
		coverImage,
		categories,
		scheduleDate,
		imageAttribution,
	} = devotionalData;

	// Calculate estimated reading time
	const wordCount =
		(content?.split(" ").length || 0) +
		(scripture?.split(" ").length || 0) +
		(prayer?.split(" ").length || 0) +
		(reflection?.split(" ").length || 0);
	const readingTime = Math.max(1, Math.ceil(wordCount / 200)); // Average reading speed 200 words/min

	return (
		<Dialog open={open} onOpenChange={onClose}>
			<DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden p-0">
				{/* Header with close button */}
				<div className="sticky top-0 z-50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b px-6 py-4">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-2">
							<Sparkles className="w-5 h-5 text-secondary" />
							<h3 className="font-semibold">Preview</h3>
						</div>
						<Button variant="ghost" size="icon" onClick={onClose}>
							<X className="w-5 h-5" />
						</Button>
					</div>
				</div>

				{/* Scrollable content */}
				<div className="overflow-y-auto max-h-[calc(90vh-80px)]">
					<article className="max-w-3xl mx-auto">
						{/* Cover Image */}
						{coverImage && (
							<div className="relative w-full aspect-video overflow-hidden">
								<img
									src={getImageUrl(coverImage)}
									alt={title || "Devotional cover"}
									className="w-full h-full object-cover"
								/>
								{imageAttribution && (
									<div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-4">
										<p className="text-white text-xs opacity-90">
											Photo by{" "}
											<a
												href={imageAttribution.url}
												target="_blank"
												rel="noopener noreferrer"
												className="underline hover:text-secondary inline-flex items-center gap-1"
											>
												{imageAttribution.photographer}
												<ExternalLink className="w-3 h-3" />
											</a>
											{" "}from Pexels
										</p>
									</div>
								)}
							</div>
						)}

						{/* Content */}
						<div className="px-6 py-8 space-y-8">
							{/* Metadata */}
							<div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
								<div className="flex items-center gap-2">
									<Calendar className="w-4 h-4" />
									<span>
										{scheduleDate
											? format(scheduleDate, "MMMM d, yyyy")
											: format(new Date(), "MMMM d, yyyy")}
									</span>
								</div>
								<div className="flex items-center gap-2">
									<Clock className="w-4 h-4" />
									<span>{readingTime} min read</span>
								</div>
								<span className="text-secondary">{authorName}</span>
							</div>

							{/* Title */}
							<motion.h1
								initial={{ opacity: 0, y: 20 }}
								animate={{ opacity: 1, y: 0 }}
								className="text-4xl md:text-5xl font-serif font-bold text-foreground leading-tight"
							>
								{title || "Untitled Devotional"}
							</motion.h1>

							{/* Categories */}
							{categories && categories.length > 0 && (
								<div className="flex flex-wrap items-center gap-2">
									<Tag className="w-4 h-4 text-muted-foreground" />
									{categories.map((category, index) => (
										<span
											key={index}
											className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-secondary/10 text-secondary capitalize"
										>
											{category}
										</span>
									))}
								</div>
							)}

							{/* Main Content */}
							<div className="space-y-6 text-lg leading-relaxed">
								{content && (
									<motion.div
										initial={{ opacity: 0 }}
										animate={{ opacity: 1 }}
										transition={{ delay: 0.1 }}
									>
										<p className="whitespace-pre-wrap">{content}</p>
									</motion.div>
								)}

								{/* Scripture */}
								{scripture && scriptureReference && (
									<motion.div
										initial={{ opacity: 0 }}
										animate={{ opacity: 1 }}
										transition={{ delay: 0.2 }}
										className="bg-secondary/5 border-l-4 border-secondary rounded-r-xl p-6 my-8"
									>
										<p className="font-serif text-xl italic text-foreground/90 mb-3">
											"{scripture}"
										</p>
										<div className="flex items-center justify-between">
											<p className="text-sm text-secondary font-medium flex items-center gap-2">
												<BookOpen className="w-4 h-4" />
												{scriptureReference}
											</p>
											{scriptureTranslation && (
												<span className="text-xs text-muted-foreground">
													{scriptureTranslation}
												</span>
											)}
										</div>
									</motion.div>
								)}

								{/* Reflection */}
								{reflection && (
									<motion.div
										initial={{ opacity: 0 }}
										animate={{ opacity: 1 }}
										transition={{ delay: 0.3 }}
									>
										<h3 className="text-xl font-semibold text-foreground mb-3">
											Reflection
										</h3>
										<p className="whitespace-pre-wrap text-foreground/90">
											{reflection}
										</p>
									</motion.div>
								)}

								{/* Prayer */}
								{prayer && (
									<motion.div
										initial={{ opacity: 0 }}
										animate={{ opacity: 1 }}
										transition={{ delay: 0.4 }}
										className="bg-accent/5 border border-accent/20 rounded-2xl p-6 my-8"
									>
										<p className="text-sm font-medium text-accent mb-2">Prayer</p>
										<p className="italic text-foreground/90 whitespace-pre-wrap">
											{prayer}
										</p>
									</motion.div>
								)}
							</div>

							{/* Empty State */}
							{!content && !scripture && !prayer && !reflection && (
								<div className="text-center py-12 text-muted-foreground">
									<BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
									<p>Start writing your devotional to see the preview</p>
								</div>
							)}
						</div>
					</article>
				</div>
			</DialogContent>
		</Dialog>
	);
}
