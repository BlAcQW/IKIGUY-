/**
 * HeroBanner Component
 * Featured book hero banner with play button and metadata
 */

import { useNavigate } from 'react-router-dom';
import { Play, Info } from 'lucide-react';
import { motion } from 'framer-motion';

interface HeroBannerProps {
	id: string;
	title: string;
	author: string;
	description: string;
	coverUrl: string;
	backgroundUrl?: string;
	duration?: number;
	genre?: string;
}

export default function HeroBanner({
	id,
	title,
	author,
	description,
	coverUrl,
	backgroundUrl,
	duration,
	genre,
}: HeroBannerProps) {
	const navigate = useNavigate();

	const formatDuration = (minutes: number) => {
		const hours = Math.floor(minutes / 60);
		const mins = minutes % 60;
		return `${hours}h ${mins}m`;
	};

	return (
		<div className="relative h-[50vh] sm:h-[60vh] md:h-[70vh] w-full overflow-hidden mb-6 sm:mb-8">
			{/* Background Image with Gradient Overlay */}
			<div className="absolute inset-0">
				<img
					src={backgroundUrl || coverUrl}
					alt={title}
					className="w-full h-full object-cover"
				/>
				{/* Gradient overlays for better text readability */}
				<div className="absolute inset-0 bg-gradient-to-r from-gray-950 via-gray-950/80 to-transparent" />
				<div className="absolute inset-0 bg-gradient-to-t from-gray-950 via-transparent to-transparent" />
			</div>

			{/* Content */}
			<div className="relative h-full flex items-center px-4 sm:px-6 md:px-8 max-w-7xl mx-auto overflow-hidden">
				<motion.div
					initial={{ opacity: 0, y: 20 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ duration: 0.8 }}
					className="max-w-2xl w-full space-y-3 sm:space-y-4 md:space-y-6 pr-2 sm:pr-0"
				>
					{/* Genre Badge */}
					{genre && (
						<div className="inline-block px-2 sm:px-4 py-1 rounded-full bg-purple-500/20 border border-purple-500/50 max-w-full">
							<span className="text-xs sm:text-sm font-semibold text-purple-300 break-words">
								{genre}
							</span>
						</div>
					)}

					{/* Title */}
					<h1 className="text-xl sm:text-4xl md:text-5xl lg:text-6xl font-bold text-white drop-shadow-lg leading-tight break-words overflow-wrap-anywhere hyphens-auto">
						{title}
					</h1>

					{/* Author */}
					<p className="text-sm sm:text-lg md:text-xl text-gray-300 break-words overflow-wrap-anywhere">
						by <span className="text-purple-400 font-semibold break-words">{author}</span>
					</p>

					{/* Duration */}
					{duration && (
						<p className="text-xs sm:text-sm text-gray-400">{formatDuration(duration)}</p>
					)}

					{/* Description - Hidden on very small screens */}
					<p className="hidden sm:block text-sm sm:text-base md:text-lg text-gray-300 line-clamp-2 md:line-clamp-3 max-w-xl break-words overflow-wrap-anywhere">
						{description}
					</p>

					{/* Action Buttons */}
					<div className="flex flex-col sm:flex-row gap-3 sm:gap-4 pt-2 sm:pt-4">
						{/* Play Button */}
						<button
							onClick={() => navigate(`/player/${id}`)}
							className="flex items-center justify-center space-x-2 sm:space-x-3 px-5 sm:px-6 md:px-8 py-3 sm:py-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-full text-white font-semibold text-sm sm:text-base md:text-lg transition transform hover:scale-105 active:scale-95 active:from-purple-700 active:to-pink-700 shadow-lg no-zoom touch-feedback"
						>
							<Play className="h-5 w-5 sm:h-6 sm:w-6 fill-white" />
							<span>Start Listening</span>
						</button>

						{/* More Info Button */}
						<button
							onClick={() => navigate(`/book/${id}`)}
							className="flex items-center justify-center space-x-2 sm:space-x-3 px-5 sm:px-6 md:px-8 py-3 sm:py-4 bg-gray-800/80 hover:bg-gray-700/80 active:bg-gray-600/80 backdrop-blur-sm rounded-full text-white font-semibold text-sm sm:text-base md:text-lg transition transform hover:scale-105 active:scale-95 border border-gray-600 no-zoom touch-feedback"
						>
							<Info className="h-5 w-5 sm:h-6 sm:w-6" />
							<span>More Info</span>
						</button>
					</div>
				</motion.div>

				{/* Book Cover (optional decorative element on the right) */}
				<motion.div
					initial={{ opacity: 0, x: 50 }}
					animate={{ opacity: 1, x: 0 }}
					transition={{ duration: 0.8, delay: 0.2 }}
					className="hidden lg:block absolute right-8 top-1/2 -translate-y-1/2"
				>
					<img
						src={coverUrl}
						alt={title}
						className="w-48 xl:w-64 h-72 xl:h-96 object-cover rounded-lg shadow-2xl"
					/>
				</motion.div>
			</div>
		</div>
	);
}
