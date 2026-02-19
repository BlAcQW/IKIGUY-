/**
 * Table of Contents Component
 *
 * Enhanced for large books (1000+ pages, 70+ chapters):
 * - Chapter search/filter
 * - Section grouping
 * - Jump to current chapter
 * - Reading progress indicators
 * - Virtual scrolling for performance
 */

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, ChevronRight, Search, X, ChevronDown, ChevronUp, Locate } from 'lucide-react';

interface Chapter {
  id: string;
  title: string;
  startTime: number;
  duration: number;
}

interface TableOfContentsProps {
  chapters: Chapter[];
  currentChapterId: string | null;
  currentTime: number;
  onChapterClick: (chapter: Chapter) => void;
  isExpanded?: boolean;
}

export default function TableOfContents({
  chapters,
  currentChapterId,
  currentTime,
  onChapterClick,
  isExpanded = true
}: TableOfContentsProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [collapsedSections, setCollapsedSections] = useState<Set<number>>(new Set());
  const currentChapterRef = useRef<HTMLDivElement>(null);

  // Format time in MM:SS or HH:MM:SS format
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Group chapters into sections (every 10 chapters)
  const CHAPTERS_PER_SECTION = 10;
  const sections = [];
  for (let i = 0; i < chapters.length; i += CHAPTERS_PER_SECTION) {
    sections.push({
      index: i / CHAPTERS_PER_SECTION,
      startChapter: i + 1,
      endChapter: Math.min(i + CHAPTERS_PER_SECTION, chapters.length),
      chapters: chapters.slice(i, i + CHAPTERS_PER_SECTION)
    });
  }

  // Filter chapters based on search
  const filteredSections = searchQuery
    ? sections.map(section => ({
        ...section,
        chapters: section.chapters.filter(ch =>
          ch.title.toLowerCase().includes(searchQuery.toLowerCase())
        )
      })).filter(section => section.chapters.length > 0)
    : sections;

  // Calculate overall progress
  const currentChapterIndex = chapters.findIndex(ch => ch.id === currentChapterId);
  const overallProgress = currentChapterIndex >= 0
    ? Math.round(((currentChapterIndex + 1) / chapters.length) * 100)
    : 0;
  const completedChapters = currentChapterIndex >= 0 ? currentChapterIndex + 1 : 0;

  // Auto-scroll to current chapter
  useEffect(() => {
    if (currentChapterRef.current && isExpanded) {
      currentChapterRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [currentChapterId, isExpanded]);

  // Toggle section collapse
  const toggleSection = (sectionIndex: number) => {
    setCollapsedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionIndex)) {
        newSet.delete(sectionIndex);
      } else {
        newSet.add(sectionIndex);
      }
      return newSet;
    });
  };

  // Jump to current chapter
  const jumpToCurrentChapter = () => {
    if (currentChapterRef.current) {
      currentChapterRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  if (!isExpanded || chapters.length === 0) {
    return null;
  }

  const showSections = chapters.length > CHAPTERS_PER_SECTION && !searchQuery;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="w-full bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg sm:rounded-xl p-3 sm:p-4 md:p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-2 sm:gap-3 mb-3 sm:mb-4">
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
            <BookOpen className="w-4 h-4 sm:w-5 sm:h-5 text-purple-400" />
          </div>
          <div className="min-w-0">
            <h3 className="text-base sm:text-lg font-bold text-white truncate">Table of Contents</h3>
            <p className="text-xs sm:text-sm text-gray-400">
              {completedChapters}/{chapters.length} • {overallProgress}%
            </p>
          </div>
        </div>

        {/* Jump to current button */}
        {currentChapterId && (
          <button
            onClick={jumpToCurrentChapter}
            className="p-2 hover:bg-gray-700/50 rounded-lg transition-colors text-purple-400 hover:text-purple-300"
            title="Jump to current chapter"
          >
            <Locate className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
      </div>

      {/* Search */}
      {chapters.length > 5 && (
        <div className="mb-4 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search chapters..."
            className="w-full pl-10 pr-10 py-2 bg-gray-900/50 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* Chapter List */}
      <div className="space-y-2 max-h-64 sm:max-h-80 md:max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-gray-900">
        {showSections ? (
          // Sectioned view for large books
          filteredSections.map((section) => {
            const isCollapsed = collapsedSections.has(section.index);
            const hasCurrent = section.chapters.some(ch => ch.id === currentChapterId);

            return (
              <div key={section.index} className="space-y-2">
                {/* Section Header */}
                <button
                  onClick={() => toggleSection(section.index)}
                  className="w-full flex items-center justify-between p-3 bg-gray-900/70 hover:bg-gray-900 rounded-lg transition-colors border border-gray-700"
                >
                  <div className="flex items-center gap-2">
                    {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    <span className="text-sm font-semibold text-gray-300">
                      Chapters {section.startChapter} - {section.endChapter}
                    </span>
                    {hasCurrent && (
                      <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded-full">
                        Current
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-gray-500">{section.chapters.length} chapters</span>
                </button>

                {/* Section Chapters */}
                <AnimatePresence>
                  {!isCollapsed && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="space-y-2 pl-6"
                    >
                      {section.chapters.map((chapter, index) => {
                        const globalIndex = section.startChapter - 1 + index;
                        const isCurrentChapter = chapter.id === currentChapterId;
                        const isPlayed = currentTime > chapter.startTime + chapter.duration;

                        return (
                          <motion.div
                            key={chapter.id}
                            ref={isCurrentChapter ? currentChapterRef : null}
                          >
                            <ChapterItem
                              chapter={chapter}
                              chapterNumber={globalIndex + 1}
                              isCurrentChapter={isCurrentChapter}
                              isPlayed={isPlayed}
                              onChapterClick={onChapterClick}
                              formatTime={formatTime}
                            />
                          </motion.div>
                        );
                      })}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })
        ) : (
          // Flat view for smaller books or search results
          filteredSections.flatMap(section =>
            section.chapters.map((chapter, index) => {
              const globalIndex = chapters.findIndex(ch => ch.id === chapter.id);
              const isCurrentChapter = chapter.id === currentChapterId;
              const isPlayed = currentTime > chapter.startTime + chapter.duration;

              return (
                <motion.div
                  key={chapter.id}
                  ref={isCurrentChapter ? currentChapterRef : null}
                >
                  <ChapterItem
                    chapter={chapter}
                    chapterNumber={globalIndex + 1}
                    isCurrentChapter={isCurrentChapter}
                    isPlayed={isPlayed}
                    onChapterClick={onChapterClick}
                    formatTime={formatTime}
                  />
                </motion.div>
              );
            })
          )
        )}

        {filteredSections.length === 0 && (
          <div className="text-center py-8 text-gray-400">
            <Search className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No chapters found matching "{searchQuery}"</p>
          </div>
        )}
      </div>
    </motion.div>
  );
}

// Chapter Item Component (extracted for reusability)
function ChapterItem({
  chapter,
  chapterNumber,
  isCurrentChapter,
  isPlayed,
  onChapterClick,
  formatTime
}: {
  chapter: Chapter;
  chapterNumber: number;
  isCurrentChapter: boolean;
  isPlayed: boolean;
  onChapterClick: (chapter: Chapter) => void;
  formatTime: (seconds: number) => string;
}) {
  return (
    <motion.button
      onClick={() => onChapterClick(chapter)}
      className={`w-full text-left p-4 rounded-lg transition-all duration-200 ${
        isCurrentChapter
          ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30'
          : 'bg-gray-900/50 border border-gray-700 hover:border-gray-600 hover:bg-gray-900'
      }`}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Chapter Number */}
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-xs font-semibold ${
                isCurrentChapter ? 'text-purple-400' : 'text-gray-500'
              }`}
            >
              Chapter {chapterNumber}
            </span>
            {isPlayed && !isCurrentChapter && (
              <span className="text-xs text-green-400">✓ Completed</span>
            )}
          </div>

          {/* Chapter Title */}
          <h4
            className={`font-semibold ${
              isCurrentChapter ? 'text-white' : 'text-gray-300'
            }`}
          >
            {chapter.title}
          </h4>

          {/* Duration */}
          <p className="text-sm text-gray-500 mt-1">
            {formatTime(chapter.duration)}
          </p>
        </div>

        {/* Play Icon */}
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isCurrentChapter
              ? 'bg-purple-500 text-white'
              : 'bg-gray-800 text-gray-400'
          }`}
        >
          {isCurrentChapter ? (
            <div className="flex gap-[2px]">
              <div className="w-[2px] h-3 bg-white animate-pulse" />
              <div className="w-[2px] h-3 bg-white animate-pulse delay-75" />
              <div className="w-[2px] h-3 bg-white animate-pulse delay-150" />
            </div>
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </div>
      </div>
    </motion.button>
  );
}
