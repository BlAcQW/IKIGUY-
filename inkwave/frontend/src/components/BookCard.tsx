/**
 * BookCard Component
 * Individual book card with cover, metadata, and progress indicator
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Clock } from 'lucide-react';
import { motion } from 'framer-motion';
import { generatePlaceholderCover } from '../lib/bookCoverUtils';

interface BookCardProps {
  id: string;
  title: string;
  author: string;
  coverUrl: string;
  duration?: number; // in minutes
  progress?: number; // 0-100
  showProgress?: boolean;
}

export default function BookCard({
  id,
  title,
  author,
  coverUrl,
  duration,
  progress = 0,
  showProgress = false,
}: BookCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [imageError, setImageError] = useState(false);
  const navigate = useNavigate();

  // Use placeholder if image fails to load or has error
  const displayCoverUrl = imageError ? generatePlaceholderCover(title, author) : coverUrl;

  const handleClick = () => {
    navigate(`/book/${id}`);
  };

  const handlePlayClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate(`/player/${id}`);
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  return (
    <motion.div
      className="flex-shrink-0 w-36 sm:w-40 md:w-44 lg:w-48 cursor-pointer group touch-card no-zoom"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
    >
      {/* Book Cover */}
      <div className="relative aspect-[2/3] rounded-lg overflow-hidden mb-3 bg-gray-800 shadow-lg">
        <img
          src={displayCoverUrl}
          alt={title}
          className="w-full h-full object-cover"
          onError={() => setImageError(true)}
        />

        {/* Play Overlay - Always visible on mobile, hover on desktop */}
        <div
          className={`absolute inset-0 bg-black/40 flex items-center justify-center transition-opacity duration-200
            md:opacity-0 md:group-hover:opacity-100 md:bg-black/60
            ${isHovered ? 'opacity-100' : 'opacity-100 md:opacity-0'}`}
        >
          <button
            onClick={handlePlayClick}
            className="p-3 sm:p-4 rounded-full bg-purple-500/90 hover:bg-purple-600 transition transform touch-button no-zoom active:scale-90 active:bg-purple-700 md:hover:scale-110"
          >
            <Play className="h-6 w-6 sm:h-8 sm:w-8 text-white fill-white" />
          </button>
        </div>

        {/* Progress Bar (if showProgress) */}
        {showProgress && progress > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-700">
            <div
              className="h-full bg-purple-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>

      {/* Book Metadata */}
      <div className="space-y-1">
        <h3 className="text-xs sm:text-sm font-semibold text-white line-clamp-2 group-hover:text-purple-400 transition">
          {title}
        </h3>
        <p className="text-[10px] sm:text-xs text-gray-400 line-clamp-1">{author}</p>

        {/* Duration or Progress Text */}
        {duration && (
          <div className="flex items-center space-x-1 text-[10px] sm:text-xs text-gray-500">
            <Clock className="h-2.5 w-2.5 sm:h-3 sm:w-3" />
            <span>{formatDuration(duration)}</span>
          </div>
        )}

        {showProgress && progress > 0 && (
          <p className="text-[10px] sm:text-xs text-purple-400">{progress}% complete</p>
        )}
      </div>
    </motion.div>
  );
}
