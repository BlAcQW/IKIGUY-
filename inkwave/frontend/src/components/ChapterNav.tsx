/**
 * ChapterNav Component
 * Chapter navigation drawer for audio player with progress indicators
 */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { List, X, Check, Play, Circle, Search, Bookmark } from 'lucide-react';

interface Chapter {
	id: string;
	title: string;
	duration: number;
	order: number;
	startTime?: number; // Start time in seconds within the full audiobook
}

interface ChapterNavProps {
	chapters: Chapter[];
	currentChapter: number; // Current chapter order (1-based)
	currentTime?: number; // Current playback position in seconds
	totalDuration?: number; // Total audiobook duration
	onSelectChapter: (chapter: Chapter) => void;
	onBookmarkChapter?: (chapter: Chapter) => void; // Optional bookmark handler
}

type ChapterStatus = 'completed' | 'in_progress' | 'unplayed';

export default function ChapterNav({
	chapters,
	currentChapter,
	currentTime = 0,
	totalDuration = 0,
	onSelectChapter,
	onBookmarkChapter,
}: ChapterNavProps) {
	const [isOpen, setIsOpen] = useState(false);
	const [searchQuery, setSearchQuery] = useState('');

	// Calculate chapter statuses based on current time
	const chapterStatuses = useMemo(() => {
		const statuses: Map<number, { status: ChapterStatus; progress: number }> = new Map();

		if (!chapters || chapters.length === 0) return statuses;

		chapters.forEach((chapter, index) => {
			const chapterStart = chapter.startTime || 0;
			const nextChapter = chapters[index + 1];
			const chapterEnd = nextChapter?.startTime || totalDuration;
			const chapterDuration = chapterEnd - chapterStart;

			if (currentTime >= chapterEnd) {
				// Completed - we've passed this chapter
				statuses.set(chapter.order, { status: 'completed', progress: 100 });
			} else if (currentTime >= chapterStart && currentTime < chapterEnd) {
				// In progress - currently in this chapter
				const progress = chapterDuration > 0
					? ((currentTime - chapterStart) / chapterDuration) * 100
					: 0;
				statuses.set(chapter.order, { status: 'in_progress', progress });
			} else {
				// Unplayed - haven't reached this chapter yet
				statuses.set(chapter.order, { status: 'unplayed', progress: 0 });
			}
		});

		return statuses;
	}, [chapters, currentTime, totalDuration]);

	const formatDuration = (seconds: number) => {
		if (seconds < 60) return `${Math.round(seconds)}s`;
		const mins = Math.floor(seconds / 60);
		const hours = Math.floor(mins / 60);
		const remainingMins = mins % 60;
		if (hours > 0) {
			return remainingMins > 0 ? `${hours}h ${remainingMins}m` : `${hours}h`;
		}
		return `${mins}m`;
	};

	// Format timestamp in HH:MM:SS or MM:SS format
	const formatTimestamp = (seconds: number) => {
		const hrs = Math.floor(seconds / 3600);
		const mins = Math.floor((seconds % 3600) / 60);
		const secs = Math.floor(seconds % 60);
		if (hrs > 0) {
			return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
		}
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	};

	// Calculate stats for header
	const stats = useMemo(() => {
		let completed = 0;
		let inProgress = 0;
		let unplayed = 0;

		chapterStatuses.forEach(({ status }) => {
			if (status === 'completed') completed++;
			else if (status === 'in_progress') inProgress++;
			else unplayed++;
		});

		return { completed, inProgress, unplayed, total: chapters?.length || 0 };
	}, [chapterStatuses, chapters]);

	// Filter chapters based on search query
	const filteredChapters = useMemo(() => {
		if (!chapters || !searchQuery.trim()) return chapters;
		const query = searchQuery.toLowerCase().trim();
		return chapters.filter(
			(chapter) =>
				chapter.title.toLowerCase().includes(query) ||
				String(chapter.order).includes(query)
		);
	}, [chapters, searchQuery]);

	// Don't render if no chapters
	if (!chapters || chapters.length === 0) {
		return null;
	}

	return (
		<>
			{/* Chapters Button with progress indicator */}
			<button
				onClick={() => setIsOpen(true)}
				className="relative p-2 bg-gray-900/60 backdrop-blur-md hover:bg-gray-800/80 rounded-full text-gray-300 hover:text-white transition-all"
				title={`Chapters (${stats.completed}/${stats.total} complete)`}
			>
				<List className="h-5 w-5" />
				{/* Progress dot indicator */}
				{stats.completed > 0 && stats.completed < stats.total && (
					<span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-purple-500 rounded-full border border-gray-900" />
				)}
				{stats.completed === stats.total && stats.total > 0 && (
					<span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-green-500 rounded-full border border-gray-900" />
				)}
			</button>

			{/* Drawer */}
			<AnimatePresence>
				{isOpen && (
					<>
						{/* Backdrop */}
						<motion.div
							initial={{ opacity: 0 }}
							animate={{ opacity: 1 }}
							exit={{ opacity: 0 }}
							onClick={() => setIsOpen(false)}
							className="fixed inset-0 bg-black/80 z-40"
						/>

						{/* Drawer Content */}
						<motion.div
							initial={{ x: '100%' }}
							animate={{ x: 0 }}
							exit={{ x: '100%' }}
							transition={{ type: 'spring', damping: 30, stiffness: 300 }}
							className="fixed right-0 top-0 bottom-0 w-full sm:w-96 bg-gray-900 shadow-2xl z-50 overflow-y-auto"
						>
							{/* Header */}
							<div className="sticky top-0 bg-gray-900 border-b border-gray-800 p-4">
								<div className="flex items-center justify-between mb-3">
									<h2 className="text-xl font-bold text-white">Chapters</h2>
									<button
										onClick={() => setIsOpen(false)}
										className="p-2 hover:bg-gray-800 rounded-lg transition"
									>
										<X className="h-5 w-5 text-gray-400" />
									</button>
								</div>

								{/* Search input - only show if many chapters */}
								{chapters.length > 5 && (
									<div className="relative mb-3">
										<Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
										<input
											type="text"
											placeholder="Search chapters..."
											value={searchQuery}
											onChange={(e) => setSearchQuery(e.target.value)}
											className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 text-sm"
										/>
										{searchQuery && (
											<button
												onClick={() => setSearchQuery('')}
												className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
											>
												<X className="h-4 w-4" />
											</button>
										)}
									</div>
								)}

								{/* Progress summary */}
								<div className="flex items-center gap-4 text-xs">
									<span className="flex items-center gap-1 text-green-400">
										<Check className="h-3 w-3" />
										{stats.completed} done
									</span>
									{stats.inProgress > 0 && (
										<span className="flex items-center gap-1 text-purple-400">
											<Play className="h-3 w-3" />
											{stats.inProgress} playing
										</span>
									)}
									<span className="flex items-center gap-1 text-gray-500">
										<Circle className="h-3 w-3" />
										{stats.unplayed} remaining
									</span>
								</div>
								{/* Overall progress bar */}
								<div className="mt-3 h-1.5 bg-gray-800 rounded-full overflow-hidden">
									<div
										className="h-full bg-gradient-to-r from-green-500 to-purple-500 transition-all duration-300"
										style={{ width: `${(stats.completed / stats.total) * 100}%` }}
									/>
								</div>

								{/* Search results count */}
								{searchQuery && (
									<p className="mt-2 text-xs text-gray-500">
										{filteredChapters.length} of {chapters.length} chapters match
									</p>
								)}
							</div>

							{/* Chapters List */}
							<div className="p-4 space-y-2">
								{filteredChapters.length === 0 && searchQuery && (
									<div className="text-center py-8 text-gray-500">
										<p>No chapters match "{searchQuery}"</p>
										<button
											onClick={() => setSearchQuery('')}
											className="mt-2 text-purple-400 hover:text-purple-300 text-sm"
										>
											Clear search
										</button>
									</div>
								)}
								{filteredChapters.map((chapter, index) => {
									const isCurrent = chapter.order === currentChapter;
									const chapterInfo = chapterStatuses.get(chapter.order);
									const status = chapterInfo?.status || 'unplayed';
									const progress = chapterInfo?.progress || 0;

									return (
										<motion.div
											key={chapter.id}
											initial={{ opacity: 0, y: 10 }}
											animate={{ opacity: 1, y: 0 }}
											transition={{ delay: index * 0.03 }}
											onClick={() => {
												onSelectChapter(chapter);
												setIsOpen(false);
											}}
											className={`relative p-4 rounded-lg cursor-pointer transition overflow-hidden ${
												isCurrent
													? 'bg-purple-500/20 border-2 border-purple-500'
													: status === 'completed'
													? 'bg-gray-800/50 border-2 border-green-500/30'
													: 'bg-gray-800 hover:bg-gray-700 border-2 border-transparent'
											}`}
										>
											{/* Progress bar background for in-progress chapters */}
											{status === 'in_progress' && (
												<div
													className="absolute inset-0 bg-purple-500/10 transition-all duration-300"
													style={{ width: `${progress}%` }}
												/>
											)}

											<div className="relative flex items-start justify-between">
												<div className="flex-1">
													<div className="flex items-center space-x-2 mb-1">
														{/* Status icon */}
														{status === 'completed' ? (
															<span className="flex items-center justify-center w-5 h-5 bg-green-500/20 rounded-full">
																<Check className="h-3 w-3 text-green-400" />
															</span>
														) : status === 'in_progress' ? (
															<span className="flex items-center justify-center w-5 h-5 bg-purple-500/20 rounded-full">
																<Play className="h-3 w-3 text-purple-400 fill-purple-400" />
															</span>
														) : (
															<span className="flex items-center justify-center w-5 h-5 bg-gray-700 rounded-full">
																<span className="text-xs font-mono text-gray-500">
																	{chapter.order}
																</span>
															</span>
														)}

														{/* Chapter number for completed/in-progress */}
														{status !== 'unplayed' && (
															<span className="text-xs font-mono text-gray-500">
																Ch. {chapter.order}
															</span>
														)}
													</div>
													<h3
														className={`font-semibold mb-1 ${
															isCurrent
																? 'text-purple-300'
																: status === 'completed'
																? 'text-gray-300'
																: 'text-white'
														}`}
													>
														{chapter.title}
													</h3>
													<div className="flex items-center gap-2 flex-wrap">
														<p className="text-sm text-gray-500">
															{formatDuration(chapter.duration * 60)}
														</p>
														{chapter.startTime !== undefined && chapter.startTime > 0 && (
															<span className="text-xs text-gray-600 font-mono">
																@ {formatTimestamp(chapter.startTime)}
															</span>
														)}
														{status === 'in_progress' && (
															<span className="text-xs text-purple-400">
																{Math.round(progress)}% complete
															</span>
														)}
													</div>
												</div>

												{/* Right side actions */}
												<div className="flex items-center gap-2">
													{/* Bookmark button */}
													{onBookmarkChapter && (
														<button
															onClick={(e) => {
																e.stopPropagation();
																onBookmarkChapter(chapter);
															}}
															className="p-1.5 rounded-full text-gray-500 hover:text-yellow-400 hover:bg-yellow-500/10 transition-colors"
															title={`Bookmark ${chapter.title}`}
														>
															<Bookmark className="h-4 w-4" />
														</button>
													)}
													{/* Playing indicator */}
													{isCurrent && (
														<span className="relative flex h-3 w-3">
															<span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
															<span className="relative inline-flex rounded-full h-3 w-3 bg-purple-500"></span>
														</span>
													)}
												</div>
											</div>
										</motion.div>
									);
								})}
							</div>
						</motion.div>
					</>
				)}
			</AnimatePresence>
		</>
	);
}
